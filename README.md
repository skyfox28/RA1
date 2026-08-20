# Rapport de zone — RA1

Application **autonome, en un seul fichier HTML** (`rapport-zone-ra1.html`)
pour générer le compte-rendu journalier de contrôle d'une zone d'entrepôt
(RA1) : pour chaque contrôle, on note l'article, l'UM, la quantité, l'action
menée, la personne, et on joint une photo ou une capture d'écran à l'appui.
En fin de journée, un compte-rendu **Word** est généré, mettant en évidence
les écarts et dérives.

Aucune installation, aucun serveur, aucune connexion internet requise :
double-cliquez sur le fichier pour l'ouvrir dans votre navigateur (Chrome,
Edge, Firefox...) et utilisez-le directement.

## Utilisation

1. Ouvrez `rapport-zone-ra1.html` dans votre navigateur.
2. Renseignez la zone (RA1 par défaut), la date et le responsable du
   contrôle.
3. **Ajoutez vos contrôles** au fur et à mesure : article, UM, quantité
   constatée, action menée (comptage, correction SAP, rangement, remontée
   qualité...), personne, statut (Conforme / Écart / Anomalie), et une ou
   plusieurs photos/captures d'écran à l'appui. L'article est optionnel :
   vous pouvez aussi enregistrer un contrôle général de zone.
4. **Importer un extrait Excel** (au besoin, optionnel) : si vous voulez
   retrouver facilement un article et sa quantité attendue, vous pouvez
   importer un extrait Excel (SAP ou autre). Les colonnes Article,
   Désignation, UM et Quantité sont détectées automatiquement ; un lien
   « Corriger les colonnes détectées » permet d'ajuster si besoin. Une fois
   importé, tapez un code article dans le champ « Article » pour voir la
   quantité attendue s'afficher automatiquement.
5. **Générer le compte-rendu Word** : télécharge le document final avec la
   synthèse (nombre de contrôles, nombre et taux de dérives, alerte si taux
   élevé), le détail des contrôles (écarts surlignés en rouge) et les
   photos.

## Points importants

- **Rien n'est envoyé sur internet** : tout le traitement (lecture d'un
  éventuel fichier Excel, calculs, génération du document) se fait dans
  votre navigateur, localement.
- **Aucune sauvegarde automatique** : les données saisies (contrôles,
  photos, import) ne sont conservées que le temps où l'onglet reste ouvert.
  Pensez à générer et télécharger le compte-rendu Word avant de fermer
  l'onglet ou le navigateur.
- Le fichier `.doc` généré s'ouvre normalement dans Microsoft Word (mise en
  page paysage, tableau des écarts, photos intégrées). Vous pouvez ensuite
  l'enregistrer au format `.docx` depuis Word si besoin.

## Développement

Le fichier livré est un assemblage de :
- la bibliothèque [SheetJS](https://sheetjs.com) (lecture des fichiers
  Excel côté navigateur), intégrée telle quelle pour un fonctionnement
  100% hors ligne ;
- le code de l'application (HTML/CSS/JS), qui peut être retrouvé et
  modifié en éditant directement le fichier `rapport-zone-ra1.html`
  (section `<style>` pour l'apparence, dernier bloc `<script>` pour la
  logique applicative).
