from datetime import date, datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class DailyReport(db.Model):
    __tablename__ = "daily_reports"
    id = db.Column(db.Integer, primary_key=True)
    zone = db.Column(db.String(50), nullable=False, default="RA1")
    report_date = db.Column(db.Date, nullable=False, default=date.today)
    author = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sap_imports = db.relationship(
        "SapImportFile", backref="report", cascade="all, delete-orphan"
    )
    movement_imports = db.relationship(
        "MovementImportFile", backref="report", cascade="all, delete-orphan"
    )
    lines = db.relationship(
        "CheckLine", backref="report", cascade="all, delete-orphan",
        order_by="CheckLine.id",
    )
    photos = db.relationship(
        "Photo", backref="report", cascade="all, delete-orphan",
        primaryjoin="and_(DailyReport.id==Photo.report_id, Photo.check_line_id==None)",
    )

    @property
    def last_sap_import(self):
        return self.sap_imports[-1] if self.sap_imports else None

    @property
    def last_movement_import(self):
        return self.movement_imports[-1] if self.movement_imports else None

    @property
    def total_lines(self):
        return len(self.lines)

    @property
    def drift_lines(self):
        return [l for l in self.lines if l.is_drift]

    @property
    def drift_rate(self):
        if not self.total_lines:
            return 0
        return round(len(self.drift_lines) / self.total_lines * 100, 1)


# ---------------------------------------------------------------------------
# Extraction LX02 : photographie du stock de la zone (article, quantité, UM,
# lot, DLC...) utilisée pour comparer le stock informatique au constat
# physique.
# ---------------------------------------------------------------------------

class SapImportFile(db.Model):
    __tablename__ = "sap_imports"
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("daily_reports.id"), nullable=False)
    original_filename = db.Column(db.String(255))
    stored_path = db.Column(db.String(500))
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)

    rows = db.relationship("SapRow", backref="import_file", cascade="all, delete-orphan")


class SapRow(db.Model):
    __tablename__ = "sap_rows"
    id = db.Column(db.Integer, primary_key=True)
    import_id = db.Column(db.Integer, db.ForeignKey("sap_imports.id"), nullable=False)

    article = db.Column(db.String(100))
    designation = db.Column(db.String(255))
    unite_stock = db.Column(db.String(100))
    type_stock = db.Column(db.String(50))
    emplacement = db.Column(db.String(50))
    quantite = db.Column(db.Float)
    um = db.Column(db.String(20))
    lot = db.Column(db.String(100))
    dlc = db.Column(db.Date)
    date_dernier_mouvement = db.Column(db.Date)


# ---------------------------------------------------------------------------
# Extraction LT27 : ordres de transfert / mouvements d'unités de stock (UM),
# utilisée pour vérifier les mouvements informatiques (qui, quand, d'où vers
# où) sur la zone.
# ---------------------------------------------------------------------------

class MovementImportFile(db.Model):
    __tablename__ = "movement_imports"
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("daily_reports.id"), nullable=False)
    original_filename = db.Column(db.String(255))
    stored_path = db.Column(db.String(500))
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)

    rows = db.relationship("MovementRow", backref="import_file", cascade="all, delete-orphan")


class MovementRow(db.Model):
    __tablename__ = "movement_rows"
    id = db.Column(db.Integer, primary_key=True)
    import_id = db.Column(db.Integer, db.ForeignKey("movement_imports.id"), nullable=False)

    numero_ot = db.Column(db.String(50))
    code_mouvement = db.Column(db.String(20))
    magasin = db.Column(db.String(20))
    article = db.Column(db.String(100))
    lot = db.Column(db.String(100))
    utilisateur = db.Column(db.String(50))
    quantite = db.Column(db.Float)
    um = db.Column(db.String(20))
    statut_ot = db.Column(db.String(20))
    type_stock = db.Column(db.String(50))

    type_magasin_origine = db.Column(db.String(20))
    emplacement_origine = db.Column(db.String(50))
    unite_stock_origine = db.Column(db.String(100))

    type_magasin_destination = db.Column(db.String(20))
    emplacement_destination = db.Column(db.String(50))
    unite_stock_destination = db.Column(db.String(100))

    date_mouvement = db.Column(db.Date)
    heure_mouvement = db.Column(db.String(20))

    def concerns(self, zone):
        zone = (zone or "").strip().upper()
        return zone in {(self.emplacement_origine or "").upper(),
                         (self.emplacement_destination or "").upper()}

    @property
    def sens(self):
        return "Entrée" if self.emplacement_destination else "Sortie"


# ---------------------------------------------------------------------------
# Lignes de contrôle (physique et/ou informatique) + photos
# ---------------------------------------------------------------------------

class CheckLine(db.Model):
    __tablename__ = "check_lines"
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("daily_reports.id"), nullable=False)
    sap_row_id = db.Column(db.Integer, db.ForeignKey("sap_rows.id"), nullable=True)
    movement_row_id = db.Column(db.Integer, db.ForeignKey("movement_rows.id"), nullable=True)

    article = db.Column(db.String(100))
    designation = db.Column(db.String(255))
    unite_stock = db.Column(db.String(100))
    um = db.Column(db.String(20))
    lot = db.Column(db.String(100))
    dlc = db.Column(db.Date)

    qte_sap = db.Column(db.Float, nullable=True)
    qte_physique = db.Column(db.Float, nullable=True)

    type_controle = db.Column(db.String(20), default="Physique")  # Physique / Informatique
    personne = db.Column(db.String(120))
    action = db.Column(db.Text)
    statut = db.Column(db.String(30), default="Conforme")
    commentaire = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sap_row = db.relationship("SapRow")
    movement_row = db.relationship("MovementRow")
    photos = db.relationship("Photo", backref="check_line", cascade="all, delete-orphan")

    @property
    def ecart(self):
        if self.qte_sap is None or self.qte_physique is None:
            return None
        return round(self.qte_physique - self.qte_sap, 3)

    @property
    def dlc_depassee(self):
        return bool(self.dlc) and self.dlc < self.report.report_date

    @property
    def is_drift(self):
        e = self.ecart
        return (e is not None and e != 0) or self.statut in ("Ecart", "Peremption", "Anomalie")


class Photo(db.Model):
    __tablename__ = "photos"
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("daily_reports.id"), nullable=False)
    check_line_id = db.Column(db.Integer, db.ForeignKey("check_lines.id"), nullable=True)
    filename = db.Column(db.String(255))
    caption = db.Column(db.String(255), default="")
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
