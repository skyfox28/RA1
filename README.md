# Rapport de zone — RA1

Application **autonome, en un seul fichier HTML** (`rapport-zone-ra1.html`) pour
générer le compte-rendu journalier de contrôle d'une zone d'entrepôt (RA1) :
constat physique (photos), rapprochement avec les extractions SAP (**LX02** —
stock, **LT27** — mouvements / unités de stock), saisie des actions et des
personnes ayant réalisé les mouvements physiques ou informatiques, et
génération d'un compte-rendu **Word** mettant en évidence les écarts et
dérives.

Aucune installation, aucun serveur, aucune connexion internet requise :
double-cliquez sur le fichier pour l'ouvrir dans votre navigateur (Chrome,
Edge, Firefox...) et utilisez-le directement.

## Utilisation

1. Ouvrez `rapport-zone-ra1.html` dans votre navigateur.
2. Renseignez la zone (RA1 par défaut), la date et le responsable du
   contrôle.
3. **Importer LX02** : chargez l'extraction Excel du stock de la zone.
   Les colonnes sont détectées automatiquement (Article, Désignation,
   Quantité, UM, Lot, DLC...) ; vérifiez/corrigez la correspondance
   proposée puis validez.
4. **Importer LT27** (optionnel) : chargez l'extraction des mouvements
   pour vérifier les mouvements informatiques (qui a fait quoi, quand, de
   quel emplacement vers quel emplacement) sur la zone.
5. **Ajouter un contrôle** : sélectionnez un article (LX02) et/ou un
   mouvement (LT27) pour pré-remplir la ligne, saisissez la quantité
   physique constatée, la personne, l'action réalisée, et joignez une
   photo si besoin. L'écart et le statut (conforme / écart / péremption)
   sont calculés automatiquement.
6. **Photos générales** : ajoutez les photos du constat physique de la
   zone (rangement, zones à risque, etc.), indépendamment d'un article
   précis.
7. **Générer le compte-rendu Word** : télécharge le document final avec
   la synthèse, le détail des écarts (surlignés en rouge) et les photos.

## Points importants

- **Rien n'est envoyé sur internet** : tout le traitement (lecture des
  fichiers Excel, calculs, génération du document) se fait dans votre
  navigateur, localement.
- **Aucune sauvegarde automatique** : les données saisies (imports,
  contrôles, photos) ne sont conservées que le temps où l'onglet reste
  ouvert. Pensez à générer et télécharger le compte-rendu Word avant de
  fermer l'onglet ou le navigateur. Si vous devez faire une pause, ne
  fermez pas l'onglet.
- Le fichier `.doc` généré s'ouvre normalement dans Microsoft Word (mise
  en page paysage, tableau des écarts, photos intégrées). Vous pouvez
  ensuite l'enregistrer au format `.docx` depuis Word si besoin.

## Adapter le mapping des colonnes

Les noms de colonnes des extractions LX02/LT27 peuvent varier légèrement
selon la configuration du poste SAP. Après l'upload, un écran de
vérification affiche la correspondance détectée automatiquement (mots-clés
sur les intitulés de colonnes) et permet de la corriger manuellement avant
l'import — aucune modification du fichier n'est nécessaire en cas
d'intitulés différents.

## Développement

Le fichier livré est un assemblage de :
- la bibliothèque [SheetJS](https://sheetjs.com) (lecture des fichiers
  Excel côté navigateur), intégrée telle quelle pour un fonctionnement
  100% hors ligne ;
- le code de l'application (HTML/CSS/JS), qui peut être retrouvé et
  modifié en éditant directement le fichier `rapport-zone-ra1.html`
  (section `<style>` pour l'apparence, dernier bloc `<script>` pour la
  logique applicative).
