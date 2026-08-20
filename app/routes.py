import os
import uuid
from datetime import date, datetime

from flask import (
    Blueprint, current_app, flash, redirect, render_template, request,
    send_file, send_from_directory, url_for,
)

from . import sap_import as sap
from .docx_report import build_report_docx
from .models import (
    CheckLine, DailyReport, MovementImportFile, MovementRow, Photo,
    SapImportFile, SapRow, db,
)

bp = Blueprint("main", __name__)

ALLOWED_SAP_EXT = {".xlsx", ".xls"}
ALLOWED_IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

LX02_ROLES = list(sap.ROLE_KEYWORDS_LX02.keys())
LT27_ROLES = list(sap.ROLE_KEYWORDS_LT27.keys())


def _ext_ok(filename, allowed):
    return os.path.splitext(filename)[1].lower() in allowed


def _save_upload(file_storage, subdir):
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], subdir)
    os.makedirs(folder, exist_ok=True)
    ext = os.path.splitext(file_storage.filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(folder, unique_name)
    file_storage.save(path)
    return os.path.join(subdir, unique_name), file_storage.filename


def _s(v):
    if v is None:
        return None
    v = str(v).strip()
    return v or None


def _f(v):
    try:
        if v in (None, ""):
            return None
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _time_str(v):
    if v is None:
        return None
    try:
        return v.strftime("%H:%M:%S")
    except AttributeError:
        return str(v)


# ---------------------------------------------------------------------------
# Rapports
# ---------------------------------------------------------------------------

@bp.route("/")
def index():
    zone_filter = request.args.get("zone", "RA1")
    reports = (
        DailyReport.query.filter(DailyReport.zone == zone_filter)
        .order_by(DailyReport.report_date.desc(), DailyReport.id.desc())
        .all()
    )
    return render_template("index.html", reports=reports, zone_filter=zone_filter)


@bp.route("/reports/new", methods=["GET", "POST"])
def report_new():
    if request.method == "POST":
        report = DailyReport(
            zone=(request.form.get("zone") or "RA1").strip() or "RA1",
            report_date=datetime.strptime(request.form["report_date"], "%Y-%m-%d").date(),
            author=(request.form.get("author") or "").strip(),
            notes=(request.form.get("notes") or "").strip(),
        )
        db.session.add(report)
        db.session.commit()
        flash("Rapport créé. Vous pouvez maintenant importer vos extractions SAP.", "success")
        return redirect(url_for("main.report_detail", report_id=report.id))
    return render_template("report_new.html", today=date.today().isoformat())


@bp.route("/reports/<int:report_id>")
def report_detail(report_id):
    report = DailyReport.query.get_or_404(report_id)
    sap_rows = report.last_sap_import.rows if report.last_sap_import else []
    movement_rows = report.last_movement_import.rows if report.last_movement_import else []

    sap_rows_json = [
        {
            "id": r.id, "article": r.article, "designation": r.designation,
            "unite_stock": r.unite_stock, "um": r.um, "quantite": r.quantite,
            "lot": r.lot, "dlc": r.dlc.isoformat() if r.dlc else None,
        }
        for r in sap_rows
    ]
    movement_rows_json = [
        {
            "id": m.id, "article": m.article, "um": m.um, "quantite": m.quantite,
            "lot": m.lot, "utilisateur": m.utilisateur,
            "unite_stock": m.unite_stock_origine or m.unite_stock_destination,
        }
        for m in movement_rows
    ]

    return render_template(
        "report_detail.html", report=report, sap_rows=sap_rows, movement_rows=movement_rows,
        sap_rows_json=sap_rows_json, movement_rows_json=movement_rows_json,
    )


@bp.route("/reports/<int:report_id>/delete", methods=["POST"])
def report_delete(report_id):
    report = DailyReport.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    flash("Rapport supprimé.", "info")
    return redirect(url_for("main.index"))


# ---------------------------------------------------------------------------
# Import extraction SAP - étape 1 : upload + détection des colonnes
# ---------------------------------------------------------------------------

@bp.route("/reports/<int:report_id>/import/<kind>", methods=["POST"])
def import_upload(report_id, kind):
    if kind not in ("lx02", "lt27"):
        flash("Type d'extraction inconnu.", "danger")
        return redirect(url_for("main.report_detail", report_id=report_id))

    report = DailyReport.query.get_or_404(report_id)
    file = request.files.get("sap_file")
    if not file or not file.filename or not _ext_ok(file.filename, ALLOWED_SAP_EXT):
        flash("Merci de sélectionner un fichier Excel (.xlsx/.xls) valide.", "danger")
        return redirect(url_for("main.report_detail", report_id=report.id))

    rel_path, original_name = _save_upload(file, f"{kind}/{report.id}")
    abs_path = os.path.join(current_app.config["UPLOAD_FOLDER"], rel_path)

    try:
        headers = sap.sniff_headers(abs_path)
        mapping = sap.guess_mapping(headers, kind)
        preview = sap.preview_rows(abs_path)
    except Exception as exc:  # fichier illisible / corrompu
        flash(f"Impossible de lire le fichier Excel : {exc}", "danger")
        return redirect(url_for("main.report_detail", report_id=report.id))

    role_labels = {r: sap.ROLE_LABELS[r] for r in (LX02_ROLES if kind == "lx02" else LT27_ROLES)}

    return render_template(
        "import_map.html", report=report, kind=kind, headers=headers, mapping=mapping,
        preview=preview, rel_path=rel_path, original_name=original_name,
        role_labels=role_labels,
    )


# ---------------------------------------------------------------------------
# Import extraction SAP - étape 2 : confirmation du mapping et import réel
# ---------------------------------------------------------------------------

@bp.route("/reports/<int:report_id>/import/<kind>/confirm", methods=["POST"])
def import_confirm(report_id, kind):
    if kind not in ("lx02", "lt27"):
        flash("Type d'extraction inconnu.", "danger")
        return redirect(url_for("main.report_detail", report_id=report_id))

    report = DailyReport.query.get_or_404(report_id)
    rel_path = request.form["rel_path"]
    original_name = request.form["original_name"]
    abs_path = os.path.join(current_app.config["UPLOAD_FOLDER"], rel_path)

    roles = LX02_ROLES if kind == "lx02" else LT27_ROLES
    mapping = {role: (request.form.get(f"map_{role}") or None) for role in roles}

    try:
        parsed = sap.parse_rows(abs_path, mapping)
    except Exception as exc:
        flash(f"Impossible d'importer le fichier : {exc}", "danger")
        return redirect(url_for("main.report_detail", report_id=report.id))

    if kind == "lx02":
        import_file = SapImportFile(
            report_id=report.id, original_filename=original_name, stored_path=rel_path
        )
        db.session.add(import_file)
        db.session.flush()
        for item in parsed:
            db.session.add(SapRow(
                import_id=import_file.id,
                article=_s(item.get("article")),
                designation=_s(item.get("designation")),
                unite_stock=_s(item.get("unite_stock")),
                type_stock=_s(item.get("type_stock")),
                emplacement=_s(item.get("emplacement")),
                quantite=_f(item.get("quantite")),
                um=_s(item.get("um")),
                lot=_s(item.get("lot")),
                dlc=sap.to_date(item.get("dlc")),
                date_dernier_mouvement=sap.to_date(item.get("date_dernier_mouvement")),
            ))
    else:
        import_file = MovementImportFile(
            report_id=report.id, original_filename=original_name, stored_path=rel_path
        )
        db.session.add(import_file)
        db.session.flush()
        for item in parsed:
            db.session.add(MovementRow(
                import_id=import_file.id,
                numero_ot=_s(item.get("numero_ot")),
                code_mouvement=_s(item.get("code_mouvement")),
                magasin=_s(item.get("magasin")),
                article=_s(item.get("article")),
                lot=_s(item.get("lot")),
                utilisateur=_s(item.get("utilisateur")),
                quantite=_f(item.get("quantite")),
                um=_s(item.get("um")),
                statut_ot=_s(item.get("statut_ot")),
                type_stock=_s(item.get("type_stock")),
                type_magasin_origine=_s(item.get("type_magasin_origine")),
                emplacement_origine=_s(item.get("emplacement_origine")),
                unite_stock_origine=_s(item.get("unite_stock_origine")),
                type_magasin_destination=_s(item.get("type_magasin_destination")),
                emplacement_destination=_s(item.get("emplacement_destination")),
                unite_stock_destination=_s(item.get("unite_stock_destination")),
                date_mouvement=sap.to_date(item.get("date_mouvement")),
                heure_mouvement=_time_str(item.get("heure_mouvement")),
            ))

    db.session.commit()
    flash(f"{len(parsed)} ligne(s) importée(s) depuis {original_name}.", "success")
    return redirect(url_for("main.report_detail", report_id=report.id))


# ---------------------------------------------------------------------------
# Lignes de contrôle
# ---------------------------------------------------------------------------

@bp.route("/reports/<int:report_id>/lines/add", methods=["POST"])
def line_add(report_id):
    report = DailyReport.query.get_or_404(report_id)

    sap_row = SapRow.query.get(request.form.get("sap_row_id")) if request.form.get("sap_row_id") else None
    movement_row = (
        MovementRow.query.get(request.form.get("movement_row_id"))
        if request.form.get("movement_row_id") else None
    )

    qte_sap_input = _f(request.form.get("qte_sap"))
    qte_sap = qte_sap_input if qte_sap_input is not None else (sap_row.quantite if sap_row else None)

    dlc_input = request.form.get("dlc")
    dlc = sap.to_date(dlc_input) if dlc_input else (sap_row.dlc if sap_row else None)

    line = CheckLine(
        report_id=report.id,
        sap_row_id=sap_row.id if sap_row else None,
        movement_row_id=movement_row.id if movement_row else None,
        article=_s(request.form.get("article")) or (sap_row.article if sap_row else (movement_row.article if movement_row else None)),
        designation=_s(request.form.get("designation")) or (sap_row.designation if sap_row else None),
        unite_stock=_s(request.form.get("unite_stock")) or (sap_row.unite_stock if sap_row else (movement_row.unite_stock_origine if movement_row else None)),
        um=_s(request.form.get("um")) or (sap_row.um if sap_row else (movement_row.um if movement_row else None)),
        lot=_s(request.form.get("lot")) or (sap_row.lot if sap_row else (movement_row.lot if movement_row else None)),
        dlc=dlc,
        qte_sap=qte_sap,
        qte_physique=_f(request.form.get("qte_physique")),
        type_controle=request.form.get("type_controle", "Physique"),
        personne=_s(request.form.get("personne")) or (movement_row.utilisateur if movement_row else None),
        action=(request.form.get("action") or "").strip(),
        commentaire=(request.form.get("commentaire") or "").strip(),
    )

    if line.qte_sap is not None and line.qte_physique is not None:
        line.statut = "Ecart" if line.ecart != 0 else "Conforme"
    else:
        line.statut = request.form.get("statut") or "Info"

    if line.dlc and line.dlc < report.report_date:
        line.statut = "Peremption"

    db.session.add(line)
    db.session.flush()

    for file in request.files.getlist("photos"):
        if file and file.filename and _ext_ok(file.filename, ALLOWED_IMG_EXT):
            rel_path, original_name = _save_upload(file, f"photos/{report.id}")
            db.session.add(Photo(
                report_id=report.id, check_line_id=line.id, filename=rel_path,
                caption=original_name,
            ))

    db.session.commit()
    return redirect(url_for("main.report_detail", report_id=report.id))


@bp.route("/reports/<int:report_id>/lines/<int:line_id>/delete", methods=["POST"])
def line_delete(report_id, line_id):
    line = CheckLine.query.get_or_404(line_id)
    db.session.delete(line)
    db.session.commit()
    return redirect(url_for("main.report_detail", report_id=report_id))


# ---------------------------------------------------------------------------
# Photos générales de la zone (constat physique du jour)
# ---------------------------------------------------------------------------

@bp.route("/reports/<int:report_id>/photos/add", methods=["POST"])
def photos_add(report_id):
    report = DailyReport.query.get_or_404(report_id)
    caption = (request.form.get("caption") or "").strip()
    count = 0
    for file in request.files.getlist("photos"):
        if file and file.filename and _ext_ok(file.filename, ALLOWED_IMG_EXT):
            rel_path, original_name = _save_upload(file, f"photos/{report.id}")
            db.session.add(Photo(report_id=report.id, filename=rel_path, caption=caption or original_name))
            count += 1
    db.session.commit()
    if count:
        flash(f"{count} photo(s) ajoutée(s).", "success")
    else:
        flash("Aucune photo valide sélectionnée.", "warning")
    return redirect(url_for("main.report_detail", report_id=report.id))


@bp.route("/reports/<int:report_id>/photos/<int:photo_id>/delete", methods=["POST"])
def photo_delete(report_id, photo_id):
    photo = Photo.query.get_or_404(photo_id)
    abs_path = os.path.join(current_app.config["UPLOAD_FOLDER"], photo.filename)
    db.session.delete(photo)
    db.session.commit()
    if os.path.exists(abs_path):
        os.remove(abs_path)
    return redirect(url_for("main.report_detail", report_id=report_id))


@bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


# ---------------------------------------------------------------------------
# Génération du compte-rendu Word
# ---------------------------------------------------------------------------

@bp.route("/reports/<int:report_id>/download")
def report_download(report_id):
    report = DailyReport.query.get_or_404(report_id)
    buffer = build_report_docx(report, current_app.config["UPLOAD_FOLDER"])
    filename = f"Rapport_{report.zone}_{report.report_date.isoformat()}.docx"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
