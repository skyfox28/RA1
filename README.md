# Rapports de zone — RA1

Application web locale pour générer le compte-rendu journalier de contrôle
d'une zone d'entrepôt (RA1) : constat physique (photos), rapprochement avec
les extractions SAP (**LX02** — stock, **LT27** — mouvements / unités de
stock), saisie des actions et des personnes ayant réalisé les mouvements
physiques ou informatiques, et génération d'un compte-rendu **Word**
mettant en évidence les écarts et dérives.

## Fonctionnalités

- Création d'un rapport journalier par zone (RA1 par défaut, mais utilisable
  pour toute autre zone).
- Import de l'extraction **LX02** (stock par article : quantité, UM, lot,
  DLC...). Les colonnes sont détectées automatiquement puis peuvent être
  corrigées à l'écran avant validation (les extractions SAP n'ont pas
  toujours exactement les mêmes intitulés selon le poste).
- Import de l'extraction **LT27** (ordres de transfert / mouvements d'unités
  de stock) : article, utilisateur ayant réalisé le mouvement, emplacement
  cédant/prenant, date et heure — permet de vérifier les mouvements
  informatiques et de suivre une unité de stock (UM) dans la zone.
- Saisie des contrôles (physiques ou informatiques) : quantité SAP vs
  quantité physique constatée (écart calculé automatiquement), DLC,
  personne ayant réalisé le mouvement, action réalisée, statut, commentaire,
  photo(s) à l'appui.
- Photos générales de la zone (constat physique du jour), indépendantes des
  lignes de contrôle.
- Génération du compte-rendu **Word (.docx)** : synthèse (nombre de
  contrôles, nombre et taux de dérives, alerte si le taux est élevé),
  tableau détaillé des écarts (lignes en rouge), photos intégrées.
- Historique des rapports par zone.

## Installation

Prérequis : Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate          # sous Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Lancement

```bash
python run.py
```

L'application est alors disponible sur http://localhost:5000

Les données sont stockées dans une base SQLite locale (`instance/ra1.db`,
créée automatiquement) et les photos/fichiers importés dans `uploads/`. Ces
deux dossiers sont ignorés par git (`.gitignore`) : pensez à les sauvegarder
vous-même si besoin (copie du dossier, ou déploiement sur un poste/serveur
partagé du site).

## Utilisation

1. **Nouveau rapport** : choisissez la date et le responsable du contrôle
   (zone RA1 pré-remplie).
2. **Importer LX02** : chargez l'extraction Excel du stock de la zone.
   Vérifiez/ajustez la correspondance des colonnes proposée, puis validez.
3. **Importer LT27** (optionnel) : chargez l'extraction des mouvements pour
   vérifier les mouvements informatiques (qui a fait quoi, quand) sur la
   zone.
4. **Ajouter un contrôle** : sélectionnez un article (LX02) et/ou un
   mouvement (LT27) pour pré-remplir la ligne, saisissez la quantité
   physique constatée, la personne, l'action réalisée, et joignez une
   photo si besoin. L'écart et le statut (conforme / écart / péremption)
   sont calculés automatiquement.
5. **Photos générales** : ajoutez les photos du constat physique de la zone
   (rangement, zones à risque, etc.), indépendamment d'un article précis.
6. **Télécharger le compte-rendu Word** : génère le document final avec la
   synthèse, le détail des écarts (surlignés) et les photos.

## Structure du projet

```
app/
  __init__.py       # création de l'application Flask (factory)
  models.py         # modèles de données (SQLAlchemy)
  routes.py         # routes web
  sap_import.py      # lecture flexible des extractions Excel LX02 / LT27
  docx_report.py     # génération du compte-rendu Word
  templates/          # pages HTML (Jinja2 + Bootstrap)
  static/             # CSS
run.py               # point d'entrée
requirements.txt
```

## Adapter le mapping des colonnes

Les noms de colonnes des extractions LX02/LT27 peuvent varier légèrement
selon la configuration du poste SAP. `app/sap_import.py` contient des
listes de mots-clés (`ROLE_KEYWORDS_LX02`, `ROLE_KEYWORDS_LT27`) utilisées
pour deviner automatiquement la bonne colonne ; en cas de désaccord,
l'écran de vérification affiché après l'upload permet de corriger
manuellement chaque colonne avant l'import.
