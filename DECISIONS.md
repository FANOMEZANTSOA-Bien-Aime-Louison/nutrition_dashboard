# DECISIONS.md — Dashboard nutrition/santé

Journal des décisions méthodologiques. Une section par étape du brief. Format par
décision : **Décision prise** · **Pourquoi** · **Alternatives envisagées** · **Bonne
pratique générale illustrée** · **Piège à éviter**.

Les principes marqués **[PRINCIPE GÉNÉRAL]** sont transférables à n'importe quel projet
de données et ne dépendent pas de ce dataset.

---

## Étape 1 — Analyse exploratoire (EDA)

### 1.1 — Produire le notebook via un script générateur (`_build_01_eda.py`)

**Décision prise**
Le notebook `notebooks/01_eda.ipynb` n'est pas édité à la main : il est généré et exécuté
par `_build_01_eda.py`, qui contient la liste ordonnée des cellules. Pour modifier le
notebook, on modifie le script puis on le relance.

**Pourquoi**
- Le notebook devient un artefact reproductible : `python _build_01_eda.py` régénère un
  résultat identique, sans état résiduel de kernel ni exécution de cellules dans le
  désordre.
- La revue de version porte sur du code Python lisible, pas sur du JSON de notebook.
- Cohérent avec la convention du projet 1 (`_build_0X_*.py`).

**Alternatives envisagées**
- *Éditer le `.ipynb` directement dans Jupyter* — écarté : historique de diffs illisible,
  risque d'exécution non linéaire, sorties qui ne correspondent plus au code affiché.
- *Script `.py` unique produisant des PNG, sans notebook* — écarté : le brief demande
  explicitement un notebook, et le format cellule + sortie inline facilite la relecture
  pas à pas exigée par le contexte pédagogique.
- *`jupytext` (paire `.py`/`.ipynb` synchronisée)* — écarté pour l'instant : dépendance
  supplémentaire pour un bénéfice que le script générateur couvre déjà.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Un notebook exécuté est une *sortie*, pas une *source*. Garder la source sous une forme
qui se relit, se diffe et se rejoue à l'identique (script, ou notebook + outil de
pairing). Le corollaire : on ne corrige jamais un résultat en retouchant la sortie, on
corrige la source et on régénère.

**Piège à éviter**
Committer un notebook dont les sorties ne proviennent pas du code actuellement affiché
(cellules ré-exécutées après édition, `Run All` oublié). Ici le script force un
`Run All` propre à chaque génération.

---

### 1.2 — Distinguer « valeur manquante » et modalité « Aucune » sur `condition`

**Décision prise**
Traiter `condition = "Aucune"` (973 lignes) comme une information présente — le patient
n'a pas de pathologie associée — et ne compter comme manquantes que les 25 lignes (1 %)
réellement vides. Les deux sont affichées séparément dans le notebook.

**Pourquoi**
Fusionner les deux reviendrait à dire « on ne sait pas » pour 998 patients alors qu'on
sait, pour 973 d'entre eux, qu'il n'y a pas de pathologie. Cela fausserait le taux de
complétude de la colonne (40 % vs 1 % de manquants) et toute décision d'imputation à
l'étape 2.

**Alternatives envisagées**
- *Convertir `"Aucune"` en `NaN`* — écarté : perte d'information réelle, gonfle
  artificiellement le taux de nulls.
- *Convertir les `NaN` en `"Aucune"` dès l'EDA* — écarté : c'est une imputation, elle a
  sa place à l'étape 2 avec sa justification, pas dans une phase de description.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Avant de compter des valeurs manquantes, vérifier ce que « manquant » veut dire pour
chaque colonne : absence de mesure, non-applicable, zéro implicite, ou catégorie
« aucun » explicite sont des cas différents qui n'appellent pas le même traitement. Un
`NaN` et une chaîne `"Aucune"`/`"N/A"`/`"0"` ne sont pas interchangeables.

**Piège à éviter**
Lancer `df.isna().mean()` et prendre le chiffre pour argent comptant sans regarder les
modalités textuelles d'une colonne catégorielle (`"Inconnu"`, `"Non renseigné"`, `""`,
`"-"` se cachent souvent parmi les valeurs « présentes »).

---

### 1.3 — Vérifier la cohérence `bmi` fourni vs IMC recalculé avec un seuil explicite

**Décision prise**
Recalculer l'IMC (`weight_kg / (height_cm/100)²`) pour les 2500 lignes, examiner la
distribution de l'écart absolu avec la colonne `bmi`, et fixer d'avance le seuil de
tolérance à 0,05 (la moitié du dernier chiffre affiché, `bmi` étant donné à une décimale).

**Pourquoi**
`bmi` est une colonne *dérivée*. Soit elle est calculée à partir des `height_cm` /
`weight_kg` fournis (et l'écart ne doit pas dépasser l'arrondi), soit elle vient d'une
autre source (autres valeurs, autre unité, saisie manuelle) et un écart structurel
signalerait un problème de qualité à traiter au nettoyage. Résultat ici : écart ≤ 0,05
sur les 2500 lignes (le seul dépassement est à `0,05000000000000071`, bruit flottant sur
un 0,05 exact). La colonne est fiable et pourra servir de contrôle croisé si taille ou
poids devaient être imputés.

**Alternatives envisagées**
- *Comparer avec une égalité stricte* — écarté : `bmi` est arrondi à une décimale,
  l'égalité stricte produirait des milliers de faux positifs.
- *Comparer sur un échantillon* — écarté : le calcul est trivial sur 2500 lignes, autant
  le faire en entier et détecter un éventuel cas isolé.
- *Ne pas vérifier et faire confiance à la colonne* — écarté : c'est précisément le type
  de contrôle de cohérence peu coûteux qui évite de bâtir une analyse sur une colonne
  corrompue.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Quand une colonne peut se déduire d'autres colonnes, la recalculer et comparer. Fixer le
seuil de tolérance *avant* de regarder le résultat, en le justifiant par la précision des
données (arrondi d'affichage, précision de l'instrument), pas en l'ajustant après coup
pour que « ça passe ».

**Piège à éviter**
Interpréter un écart entièrement explicable par l'arrondi comme une anomalie, et lancer
un « nettoyage » qui dégrade des données saines. L'inverse est vrai aussi : un écart réel
noyé dans une moyenne proche de zéro — d'où l'examen de la distribution complète et du
max, pas seulement de la moyenne.

---

### 1.4 — Repérer les valeurs aberrantes en EDA, mais ne pas les corriger

**Décision prise**
Le notebook liste les valeurs hors plage plausible (1 apport protéique négatif + 3 sous
5 g/j ; 2 apports sodiques négatifs + 2 sous 100 mg/j ; 20 apports sodiques > 5000 mg/j)
et les patients concernés, sans appliquer aucune correction ni suppression à ce stade.

**Pourquoi**
L'EDA sert à *constater* l'état des données. La correction (plafonnement, mise à `NaN`
puis imputation, suppression) est une décision qui change les données et doit être
justifiée colonne par colonne — c'est l'objet de l'étape 2. Mélanger les deux rendrait
la description non reproductible et masquerait l'ampleur réelle du problème.

**Alternatives envisagées**
- *Corriger à la volée dans le notebook EDA* — écarté : brouille la frontière
  constat/traitement, et le lecteur ne voit plus les données brutes.
- *Ignorer les valeurs négatives puisque « c'est synthétique »* — écarté : elles sont
  injectées volontairement justement pour être détectées et traitées.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Séparer la phase qui *décrit* les données de la phase qui les *modifie*. Une EDA se
relance sur la donnée brute et donne toujours le même diagnostic ; le nettoyage est un
artefact daté et justifié qui vient après.

**Piège à éviter**
Utiliser des bornes « rondes » (`age > 90`, `sodium > 5000`) comme des vérités
physiologiques. Ici elles servent uniquement de projecteur pour inspecter les queues de
distribution ; les vrais seuils de traitement seront fixés et argumentés à l'étape 2.

---

### 1.5 — Inspecter la matrice de corrélation pour qualifier les variables d'évolution

**Décision prise**
Calculer et afficher la matrice de corrélation de Pearson entre les 10 variables
numériques, et en tirer une conclusion explicite : `weight_change_pct` et
`nutritionist_visits` ne sont corrélées à aucune autre variable (|r| ≤ 0,03), y compris
`follow_up_weeks` et `daily_calories`.

**Pourquoi**
Le dashboard (étapes 4-5) montrera l'« évolution du poids » de la patientèle. Savoir dès
l'EDA que cette colonne se comporte comme du bruit non relié aux profils empêche de
construire plus tard une visualisation qui suggérerait une relation (« plus de visites →
plus de perte de poids ») que les données ne portent pas.

**Alternatives envisagées**
- *Ne regarder les corrélations qu'au moment de concevoir les graphes* — écarté : le
  constat oriente la conception, autant l'avoir en main tôt.
- *Corrélation de Spearman* — retenue comme complément possible à l'étape 4 si une
  relation non linéaire est suspectée ; Pearson suffit pour le constat « aucune relation
  linéaire nette » à ce stade.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
En EDA, vérifier non seulement la forme de chaque variable isolée mais aussi l'absence
(ou la présence) de relations entre elles. Une variable non corrélée à quoi que ce soit
limite ce qu'un graphique peut honnêtement raconter — c'est une information de
conception, pas seulement une statistique.

**Piège à éviter**
Présenter dans un dashboard deux variables côte à côte (nuage de points, courbes
superposées) laisse le lecteur *inférer* un lien. Si les données ne montrent pas ce lien,
la visualisation ment par insinuation. À anticiper dès maintenant, pas à corriger après
retour d'un lecteur.

---

### 1.6 — Séparation apprentissage / portfolio dès la première écriture

**Décision prise**
Aucune explication pédagogique, aucune mention d'un assistant, aucun « comme demandé »
dans le code, les docstrings ou les cellules markdown du notebook. Tout le raisonnement
va dans ce fichier. Le notebook ne contient que des titres descriptifs et une section
« Observations » factuelle.

**Pourquoi**
Le brief impose deux versions finales (`-learning/` et `-portfolio/`) anticipées, pas
reconstruites à la fin. Retirer après coup le ton pédagogique disséminé dans 50 cellules
est coûteux et risqué (on en oublie). L'écrire proprement du premier coup est gratuit.

**Alternatives envisagées**
- *Commenter abondamment le notebook puis nettoyer avant la scission* — écarté
  explicitement par le brief (« pas un ajustement après coup »).
- *Deux notebooks parallèles dès maintenant* — écarté : duplication prématurée, le code
  d'analyse est identique dans les deux versions ; seul l'habillage documentaire diffère.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Décider tôt de la frontière entre le livrable et son commentaire, et la tenir à chaque
fichier écrit. Le code explique *ce qu'il fait* ; un document séparé explique *pourquoi
ces choix*. Les fusionner oblige un jour à les défusionner.

**Piège à éviter**
Le ton pédagogique qui s'infiltre dans les noms de variables (`df_apres_nettoyage_pour_comprendre`),
les docstrings (« ici on montre que… ») et les messages de commit. Se relire avec la
question « est-ce que ça a du sens pour quelqu'un qui découvre le repo sans le brief ? ».

---

## Étape 2 — Nettoyage

Entrée `data/patients_nutrition.csv` → sortie `data/patients_nutrition_clean.csv`
(2500 lignes conservées, 18 colonnes : 15 d'origine + 3 indicatrices `*_imputed`,
0 valeur manquante). Notebook : `notebooks/02_cleaning.ipynb`, généré par
`_build_02_cleaning.py`.

### 2.1 — Erreur de saisie vs valeur extrême réelle : deux traitements opposés

**Décision prise**
Trier les valeurs suspectes en deux familles, traitées différemment :
- **erreur de saisie** = valeur physiquement impossible (`daily_protein_g` ou
  `daily_sodium_mg` négatif) ou incompatible avec toute alimentation
  (`daily_protein_g` < 5 g/j, `daily_sodium_mg` < 100 mg/j) → requalifiée en `NaN`,
  puis imputée comme un manque ordinaire. 4 + 4 lignes concernées.
- **valeur extrême réelle** = rare mais physiologiquement atteignable
  (`daily_sodium_mg` entre 5000 et 6405 mg/j, 20 lignes) → **conservée sans
  modification**.

**Pourquoi**
Ces deux familles ont des causes différentes et demandent des corrections opposées.
Une valeur négative pour une quantité d'apport n'a aucune interprétation possible :
elle est certainement fausse, la garder polluerait toute statistique. Une valeur
haute mais plausible est une observation : un apport sodique de 6 g/j s'obtient avec
une alimentation très transformée, et pour un patient sous régime « Sans sel » c'est
un signal de non-adhérence — exactement ce qu'un tableau de bord de diététique doit
pouvoir montrer. La supprimer ou l'écrêter reviendrait à effacer de l'information
clinique réelle.

**Comment la plausibilité des 20 valeurs hautes a été vérifiée** (avant de décider) :
1. tri des 30 plus hautes valeurs → la queue est **continue**
   (`… 4954, 4966, 4998, 5060, 5073, 5086 …`), sans saut qui trahirait un autre
   processus (erreur de facteur 10, confusion d'unité mg/g) ;
2. `p95 = 4246`, `p99 = 4950`, `max = 6405` → pas de décrochage ;
3. les 20 valeurs se répartissent sur tous les régimes et pathologies, pas de
   concentration dans une cellule absurde ;
4. borne haute cohérente avec la littérature nutritionnelle (2 à 3× le repère de
   2300 mg/j est courant).

**Alternatives envisagées**
- *Écrêtage (capping) au p99 ou à 3 écarts-types* — écarté : fabrique une valeur qui
  n'a pas été observée, aligne artificiellement des patients distincts sur une même
  borne, et détruit le signal de non-adhérence. L'écrêtage se justifie quand une
  valeur extrême casse un modèle sensible aux grands nombres (régression non
  robuste) ; ici l'usage est descriptif et un dashboard peut afficher une queue.
- *Suppression des lignes concernées* — écarté : perte d'information sur toutes les
  autres colonnes de ces patients, pour des valeurs qui ne sont pas fausses.
- *Traiter les valeurs hautes comme les négatives (tout en erreur)* — écarté :
  reviendrait à confondre « impossible » et « rare ».
- *Winsorisation* (remplacer par le quantile sans supprimer) — même objection que
  l'écrêtage pour un usage descriptif.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
« Valeur atypique » n'est pas un diagnostic. Avant de toucher à une valeur
extrême, se demander *pourquoi* elle est là : impossible physiquement (→ erreur,
requalifier), incompatible avec le contexte métier (→ suspect, vérifier), ou
simplement dans la queue d'une vraie distribution (→ garder). Un test négatif est
une preuve d'erreur ; une valeur haute n'est qu'une invitation à vérifier. Fixer les
seuils et la règle *avant* de regarder combien de lignes tombent de chaque côté.

**Piège à éviter**
Appliquer un détecteur d'outliers générique (IQR, z-score, `IsolationForest`) puis
supprimer ou écrêter tout ce qu'il signale. Ces méthodes répondent à « quelles
valeurs sont loin du centre ? », pas à « quelles valeurs sont fausses ? ». Sur ce
jeu, elles auraient noyé les 4 négatives certaines parmi 20+ valeurs hautes
légitimes et traité les deux pareil.

### 2.2 — `condition` manquante : modalité explicite plutôt que mode ou suppression

**Décision prise**
Les 25 `condition` manquantes deviennent une modalité `Non renseigné`, distincte de
`Aucune`.

**Pourquoi**
`Aucune` = « on sait qu'il n'y a pas de pathologie associée ». Le manque = « on ne
sait pas ». Imputer par le mode (`Aucune`) écrirait une affirmation non vérifiée
dans 25 dossiers et gonflerait la part « sans pathologie » affichée au dashboard.
Une modalité explicite garde l'incertitude visible et laisse l'utilisateur la
filtrer.

**Alternatives envisagées**
- *Imputer le mode `Aucune`* — écarté : transforme une absence d'information en
  information, biais direct sur un indicateur clé.
- *Imputer par une règle métier* (p. ex. `Sans sel` → `Hypertension`) — écarté : les
  25 manques se répartissent sur tous les régimes, aucune règle fiable, et cela
  reviendrait à inventer des diagnostics.
- *Supprimer les 25 lignes* — écarté : 1 % de la base perdu sur toutes les colonnes
  pour un gain nul.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Pour une variable catégorielle, « inconnu » est souvent une modalité légitime, pas un
trou à boucher. L'imputer par le mode est le réflexe le plus courant et le plus
trompeur : il concentre l'incertitude sur la valeur la plus fréquente, précisément
là où elle se voit le moins.

**Piège à éviter**
Se retrouver avec deux encodages du même concept (`Aucune` et `Non renseigné`)
utilisés de façon interchangeable plus loin dans le code. Ils sont distincts : tout
agrégat « part de patients sans pathologie » doit compter `Aucune` et *exclure*
`Non renseigné`.

### 2.3 — Granularité de la médiane décidée par test statistique, pas par défaut

**Décision prise**
Imputer les trois colonnes numériques par une médiane, mais choisir *quelle* médiane
sur preuve (test de Kruskal-Wallis des différences entre `diet_type`) :
- `daily_protein_g` (p = 0,56) → **médiane globale** (65,5 g), 104 valeurs ;
- `daily_sodium_mg` (p = 0,31) → **médiane globale** (2820 mg), 154 valeurs ;
- `weight_change_pct` (p ≈ 3 × 10⁻³⁴) → **médiane par `diet_type`**
  (Hypocalorique −1,92 %, Hyperprotéiné −0,92 %, autres ≈ 0), 225 valeurs.

**Pourquoi**
Le brief interdit « une méthode unique appliquée partout par défaut ». Ici la
méthode de base est la même (médiane, robuste, pas de valeur inventée), mais la
granularité change selon ce que les données portent. Pour `weight_change_pct`, la
différence entre régimes est massive et attendue cliniquement (un régime
hypocalorique fait perdre du poids) : imputer les 56 patients hypocaloriques
manquants avec la médiane globale (−0,49) au lieu de leur médiane de groupe (−1,92)
raboterait l'effet régime → perte de poids que le dashboard doit montrer. Contrôle
après coup : la moyenne de `weight_change_pct` par régime est inchangée
(Hypocalorique −2,11 % avant → −2,09 % après). Pour protéines et sodium, il n'y a
pas de différence entre groupes : la médiane globale suffit et l'imputation
stratifiée n'apporterait que du bruit d'échantillonnage.

**Alternatives envisagées**
- *Moyenne au lieu de médiane* — écartée : `daily_sodium_mg` est asymétrique à
  droite (queue jusqu'à 6405), la moyenne est tirée vers le haut ; la médiane est
  neutre aussi pour les deux distributions symétriques.
- *Imputation par modèle (KNN, régression sur les autres colonnes)* — écartée :
  corrélations de `daily_protein_g`, `daily_sodium_mg`, `weight_change_pct` avec
  `age`, `bmi`, `daily_calories`, `follow_up_weeks` toutes |r| ≤ 0,03. Aucun signal
  à emprunter, un modèle ne ferait que reproduire la moyenne conditionnelle ≈ moyenne
  globale, avec plus de complexité et un risque de fuite.
- *Imputation stochastique* (tirage aléatoire dans la distribution observée) —
  écartée : préserve mieux la forme mais rend le résultat non déterministe et
  introduit une variance artificielle non traçable ; le drapeau `*_imputed` (2.4)
  répond au même besoin de façon explicite.
- *Stratifier aussi protéines/sodium par `diet_type`* — écartée sur la base du test
  (p > 0,3) : découper en 5 sous-échantillons pour estimer des médianes qui ne
  diffèrent pas ajoute du bruit sans bénéfice.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Le choix « imputation globale vs par sous-groupe » se tranche en testant si les
sous-groupes diffèrent réellement (test non paramétrique adapté, ou simple
comparaison écart-entre-groupes / écart-type intra-groupe), pas à l'intuition.
Stratifier sans différence réelle dégrade l'estimation ; ne pas stratifier quand la
différence est réelle efface un effet. La même règle vaut pour choisir moyenne vs
médiane (regarder l'asymétrie) et modèle vs constante (regarder les corrélations).

**Piège à éviter**
Imputer avec une statistique calculée sur l'ensemble du jeu *après* avoir mélangé
des sous-populations dont on montrera ensuite qu'elles diffèrent. On lisse alors la
donnée vers un centre qui ne correspond à aucun patient réel, et l'analyse
comparative en aval hérite d'un biais introduit par le nettoyage lui-même.

### 2.4 — Colonnes indicatrices `*_imputed` et distribution brute vs imputée

**Décision prise**
Ajouter `daily_protein_g_imputed`, `daily_sodium_mg_imputed`,
`weight_change_pct_imputed` (booléens) avant d'imputer. Les valeurs imputées restent
identifiables ligne par ligne.

**Pourquoi**
L'imputation par la médiane crée un pic artificiel à la médiane et réduit
l'écart-type (ici de 2 à 5 % selon la colonne). Un histogramme post-imputation
donne une fausse impression de concentration. Le drapeau permet aux visualisations
de distribution du dashboard d'exclure les lignes imputées, tandis que les usages
agrégés (comptages par régime, filtres, moyennes de groupe) peuvent les garder sans
dommage.

**Alternatives envisagées**
- *Ne rien marquer* — écarté : l'information « cette valeur est fabriquée » devient
  irrécupérable en aval, on ne peut plus produire une distribution honnête.
- *Garder les `NaN` et ne jamais imputer* — écarté : casse les filtres et agrégats
  du dashboard, et 9 % de `weight_change_pct` manquant est trop pour être ignoré
  silencieusement.
- *Deux jeux de données (avec / sans imputation)* — écarté : le drapeau dans un seul
  fichier fait le même travail sans multiplier les fichiers à garder synchrones.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL, attendu au brief]**
Une donnée imputée doit rester traçable. Le corollaire pour un tableau de bord :
choisir consciemment entre **distribution brute** (seulement les valeurs observées —
honnête sur la forme, mais l'effectif varie d'un graphe à l'autre) et **distribution
après imputation** (effectif constant, mais forme déformée par le pic artificiel).
Un lecteur non technique lit un histogramme comme « la réalité » : s'il voit un pic
à la médiane dû à l'imputation, il conclura à tort que « beaucoup de patients sont
exactement dans la moyenne ». Le défaut retenu pour ce dashboard : distributions sur
valeurs observées (drapeau `*_imputed` filtré), effectif affiché explicitement ;
imputation réservée aux agrégats et indicateurs combinés.

**Piège à éviter**
Construire un histogramme ou une boîte à moustaches sur une colonne fraîchement
imputée par une constante et le présenter tel quel. Le pic à la médiane sera lu
comme un phénomène réel de la patientèle.

### 2.5 — Aucune ligne supprimée, aucune valeur écrêtée sur les autres colonnes

**Décision prise**
Ne supprimer aucune ligne. Sur `age`, `bmi`, `daily_calories`, `height_cm`,
`weight_kg`, `follow_up_weeks`, `nutritionist_visits` : contrôle des bornes
uniquement, aucune correction (aucune valeur impossible trouvée — `bmi` min 15 =
maigreur sévère mais réelle, `daily_calories` min 900 = régime hypocalorique
encadré). Doublons : aucun.

**Pourquoi**
Le nettoyage doit être minimal et justifié : on ne touche qu'à ce qui est
démontrablement faux. Élargir les seuils « pour faire propre » retirerait des
patients réels (les cas sévères sont souvent les plus intéressants pour un service
clinique) et fausserait les effectifs.

**Alternatives envisagées**
- *Retirer les IMC < 16 ou les apports < 1000 kcal comme « aberrants »* — écarté :
  ce sont des profils cliniques plausibles et pertinents, pas des erreurs.
- *Supprimer toute ligne ayant eu au moins une imputation* — écarté : 465 lignes
  (19 %) perdues, dont l'essentiel des colonnes est valide.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Le nettoyage par défaut est *ne rien faire* ; chaque suppression ou correction doit
pouvoir être défendue individuellement. Distinguer « la valeur est fausse » de « la
valeur me gêne ».

**Piège à éviter**
Confondre nettoyage et cadrage de l'analyse. Restreindre l'étude aux adultes de
poids « normal » est une décision de périmètre, à assumer et documenter comme telle,
pas à glisser dans une étape de nettoyage sous le nom d'« outliers ».

---

## Étape 3 — Feature engineering

Entrée `data/patients_nutrition_clean.csv` (18 colonnes) → sortie
`data/patients_nutrition_features.csv` (27 colonnes, 2500 lignes, 0 valeur
manquante). Notebook : `notebooks/03_features.ipynb`, généré par
`_build_03_features.py`.

Trois indicateurs retenus (`bmi_category`, `protein_per_kg`, `risk_screen_score` et
ses colonnes de détail) ; deux pistes écartées et documentées.

### 3.1 — `bmi_category` : seuils normatifs externes plutôt que découpage empirique

**Décision prise**
Découper `bmi` selon les quatre classes de l'OMS (< 18,5 / [18,5 ; 25[ / [25 ; 30[ /
≥ 30), en catégorielle **ordonnée**. Effectifs : Corpulence normale 1513, Surpoids
852, Obésité 68, Insuffisance pondérale 67.

**Pourquoi**
Un·e diététicien·ne raisonne en statut pondéral, pas en valeur d'IMC continue. Les
seuils OMS sont partagés, documentés et compris hors de l'équipe technique : un
regroupement sur ces bornes se lit sans légende. Ils rendent possibles les filtres
et les croisements (IMC × régime, IMC × pathologie) qui structureront le dashboard.

**Alternatives envisagées**
- *Bornes empiriques (quartiles, `qcut`)* — écarté : des groupes « 25 % les plus
  maigres » n'ont pas de sens clinique et changeraient d'un échantillon à l'autre ;
  impossible à comparer à une autre patientèle ou à une norme.
- *Garder `bmi` en continu uniquement* — écarté : utile pour les distributions, mais
  ne fournit pas l'axe catégoriel nécessaire aux regroupements et aux filtres.
- *Sous-découper l'obésité (I / II / III)* — écarté ici : 68 patients en obésité,
  sous-classer produirait des effectifs trop faibles pour un graphique lisible ; la
  granularité fine relève du dossier individuel, pas d'un tableau de tendances.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Quand une variable continue possède des seuils normatifs reconnus dans le domaine
(OMS, seuils réglementaires, références médicales), discrétiser sur ces seuils plutôt
que sur la distribution de l'échantillon. On gagne la comparabilité externe et une
étiquette que le lecteur métier interprète sans apprentissage ; on perd seulement une
granularité que ce type de restitution n'exploite pas.

**Piège à éviter**
Nommer une catégorie dérivée comme une colonne existante porteuse d'un autre sens.
Ici `bmi_category = Obésité` (68 patients, IMC mesuré ≥ 30) est distinct de
`condition = Obésité` (348 patients, diagnostic saisi). Sur ce jeu synthétique les
deux ne coïncident pas (211 patients `condition = Obésité` ont une corpulence
normale). Tout agrégat doit préciser lequel des deux il compte ; le dashboard ne doit
jamais présenter l'un pour l'autre.

### 3.2 — `protein_per_kg` : rapporter l'apport à la bonne unité métier

**Décision prise**
Créer `protein_per_kg = daily_protein_g / weight_kg` (précision complète conservée),
avec `protein_per_kg_imputed` recopié de `daily_protein_g_imputed`. Médiane ≈ 0,97 ;
687 patients sous 0,8 g/kg (sur donnée observée).

**Pourquoi**
L'adéquation protéique se juge par kilogramme de poids corporel : l'apport de
référence adulte (OMS/FAO/UNU, EFSA) est ≈ 0,8 g/kg/j. « 60 g/j » ne veut rien dire
sans le poids — c'est suffisant pour une personne de 60 kg, insuffisant pour une
personne de 90 kg. L'indicateur permet une lecture directe (« part de la patientèle
sous le seuil de référence ») et un filtre par palier, impossibles avec les grammes
bruts.

**Alternatives envisagées**
- *Garder `daily_protein_g` seul* — écarté : non comparable entre patients de
  corpulences différentes.
- *Rapporter aux calories (part des apports énergétiques d'origine protéique)* —
  complément possible plus tard, mais répond à une autre question (équilibre du
  régime) et non à l'adéquation par rapport aux besoins ; le poids est le
  dénominateur des recommandations.
- *Fusionner directement dans le score de risque sans colonne dédiée* — écarté :
  `protein_per_kg` a une valeur d'affichage propre (distribution, filtre) au-delà du
  drapeau binaire.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Une quantité brute doit souvent être normalisée par la grandeur à laquelle la
référence du domaine la rapporte (par kg, par 1000 kcal, par m², par habitant, par
heure travaillée) avant d'être interprétable. Choisir le dénominateur d'après la
définition de la norme, pas d'après ce qui est le plus simple à calculer.

**Piège à éviter**
Produire un ratio sans propager le marqueur d'imputation de son numérateur. Ici
`daily_protein_g` est imputé sur 104 lignes ; sans `protein_per_kg_imputed`, une
distribution de `protein_per_kg` mélangerait valeurs mesurées et valeurs fabriquées
sans moyen de les séparer (règle 2.4).

### 3.3 — `risk_screen_score` : composite règle-à-règle, orienté triage, imputation-aware

**Décision prise**
Créer un score entier 0–4 = somme de quatre drapeaux booléens, chacun exposé dans sa
propre colonne :

| Drapeau | Règle | Seuil justifié par | n |
|---|---|---|---|
| `flag_underweight_or_obese` | `bmi_category` ∈ {Insuffisance pondérale, Obésité} | seuils OMS | 135 |
| `flag_protein_low` | `protein_per_kg` < 0,8 et non imputé | apport de référence adulte OMS/EFSA | 687 |
| `flag_sodium_high_cardiorenal` | `daily_sodium_mg` > 3500 et `condition` ∈ {Hypertension, Insuffisance rénale} et non imputé | cible < 2000–2300 mg pour ces pathologies ; 3500 = excès net | 130 |
| `flag_weight_change_marked` | `abs(weight_change_pct)` > 5 et non imputé | variation pondérale cliniquement notable (seuil usuel des outils de dépistage type MUST) | 264 |

Plus `risk_screen_incomplete` (booléen) : vrai si une colonne pouvant contribuer au
score de ce patient a été imputée (`daily_protein_g`, ou `daily_sodium_mg` si
cardio-rénal, ou `weight_change_pct`). Distribution du score : 1438 / 911 / 148 / 3.
Score ≥ 2 : 151 patients (6 %), dont 140 sur données complètes. `incomplete` : 351.

**Pourquoi**
Le contexte du brief cite explicitement des « indicateurs à risque » pour la
visualisation de la patientèle. Une file active de 2500 dossiers doit se
**prioriser** : un compteur de signaux d'alerte cumulés répond à « quels dossiers
revoir en premier ? ». Le choix d'un composite **règle-à-règle** (somme de seuils
transparents) et non d'un modèle est délibéré :
1. chaque drapeau est justifiable seul et vérifiable à la main ;
2. l'EDA a montré une absence de structure entre variables (|r| ≤ 0,03) — un modèle
   n'aurait aucun signal à apprendre ;
3. un score transparent s'explique à un·e diététicien·ne et se conteste dossier par
   dossier ; un score de modèle est une boîte noire dans un contexte clinique.

Le score est cadré comme **outil de tri, pas comme diagnostic ni échelle de
gravité** — cohérent avec la limite « pas de recommandation clinique automatisée » à
inscrire dans le README final.

**Application de la règle 2.4** : un drapeau n'est jamais levé sur une valeur
imputée (`& ~*_imputed`). Le score est donc calculé sur donnée observée uniquement et
ne peut pas *sur*-estimer le risque à partir de valeurs fabriquées. Le risque
résiduel — *sous*-estimer parce qu'une valeur manquante aurait pu déclencher un
drapeau — est rendu visible par `risk_screen_incomplete`, qui permet au dashboard de
séparer « score ≥ 2 & complet » (triage sûr) de « incomplet » (à compléter côté
données avant de conclure).

**Alternatives envisagées**
- *Score pondéré (poids différents par drapeau)* — écarté : les poids seraient
  arbitraires sans données d'issue pour les calibrer ; la somme non pondérée est
  honnête sur ce qu'elle est (un décompte).
- *Modèle de risque (régression logistique, gradient boosting)* — écarté : pas de
  variable cible, pas de corrélations exploitables, opacité inadaptée au contexte.
- *Drapeau levé aussi sur valeur imputée, avec pondération réduite* — écarté :
  complexité pour un gain nul, et brouille la garantie « aucun drapeau sur donnée
  fabriquée ».
- *Ne pas produire de composite du tout* — envisagé sérieusement (cf. pistes
  écartées du projet 1) ; retenu quand même car la justification métier (triage
  d'une grande file) est solide et indépendante de la qualité prédictive du jeu.
- *Inclure un drapeau « âgé + IMC bas » (fragilité)* — reporté : pertinent
  cliniquement mais redondant partiellement avec `flag_underweight_or_obese` ; à
  rediscuter si le dashboard révèle un besoin.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Un indicateur composite de dépistage n'exige pas que ses composantes soient
corrélées entre elles : c'est un décompte de critères, pas un facteur latent. Le
construire règle-à-règle avec chaque critère exposé séparément le rend auditable et
révisable. Et quand des entrées sont imputées : ne déclencher un critère que sur
donnée observée (jamais de sur-alerte fabriquée), et marquer explicitement les cas
où le résultat peut être sous-estimé.

**Piège à éviter**
Présenter un score de tri comme une mesure de gravité ou une recommandation. La
frontière tient au vocabulaire (« dossiers à revoir en priorité », pas « patients à
risque élevé ») et à l'exposition des drapeaux sous-jacents pour que l'utilisateur
voie *pourquoi* un dossier remonte. Deuxième piège : agréger des drapeaux dont
certains sont calculés sur des valeurs imputées, sans le signaler — le score paraît
comparable d'un patient à l'autre alors qu'il ne l'est pas.

### 3.4 — Piste écartée : découpage de `follow_up_weeks` en tranches

**Décision prise**
Ne pas créer de `follow_up_group`. `follow_up_weeks` est conservée telle quelle.

**Pourquoi**
Test réalisé avant de décider :
- distribution **indistinguable d'une loi uniforme** sur 1–25 semaines (χ² d'ajustement
  p ≈ 0,49) — aucun regroupement naturel, aucune rupture ;
- corrélation ≈ 0 avec `nutritionist_visits` (−0,04), `weight_change_pct` (−0,01),
  `daily_calories` (−0,03), et la durée calendaire depuis l'admission (−0,02).

Des tranches donneraient donc des bornes arbitraires séparant des groupes qui ne se
distinguent sur aucun indicateur du jeu. Le bénéfice attendu d'un binning (capturer
une non-linéarité, isoler un segment métier) est absent ici.

**Comparaison explicite avec `tenure_group` (projet churn)** : là, la tenure était
fortement asymétrique (masse de clients récents), fortement liée au churn, et le
binning capturait un effet de seuil réel (« premiers mois à risque »). Ici, ni
l'asymétrie ni le lien à une issue n'existent. La même transformation est utile dans
un cas, inutile dans l'autre — c'est la distribution et les relations observées qui
tranchent, pas l'habitude.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Une recette de feature engineering qui a marché sur un projet n'est pas
transférable par défaut. Avant de rejouer un binning, vérifier les deux conditions
qui le rendaient utile : une distribution avec structure (asymétrie, seuils,
multimodalité) et un lien à ce qu'on cherche à expliquer ou à segmenter. Sans elles,
le binning ajoute une colonne et retire de l'information.

**Piège à éviter**
Créer des tranches « pour avoir une variable catégorielle de plus » et s'en servir
comme filtre dans le dashboard : l'utilisateur croira que « suivi court / long » est
un axe pertinent alors que les groupes sont interchangeables.

### 3.5 — Piste écartée : ancienneté calendaire depuis l'admission

**Décision prise**
Ne pas créer de `anciennete_mois` (ni tranche associée). `admission_date` est
conservée telle quelle pour les vues temporelles (admissions par mois / trimestre).

**Pourquoi**
`mois_depuis_admission` mesurerait une grandeur réelle et différente de
`follow_up_weeks` (2–20 mois contre 0,25–6 mois). Mais elle se calcule par rapport à
une date « aujourd'hui » qui, sur un dataset synthétique figé, est arbitraire : la
feature décrirait une file active fictive et **changerait de valeur à chaque
consultation du dashboard**. Le brief pose déjà comme limite que le suivi est
« simulé, pas mesuré dans le temps » ; fabriquer une ancienneté qui dépend de
l'horloge donnerait une fausse impression de cohorte vivante.

**Alternatives envisagées**
- *Figer une date de référence (p. ex. dernière admission + 1 jour)* — écarté :
  masque le problème sans le résoudre, la date reste conventionnelle et non
  interprétable.
- *Utiliser `admission_date` en clair pour des séries temporelles d'admissions* —
  **retenu** : c'est l'usage honnête de cette colonne (flux d'entrée dans le
  service), sans prétendre suivre des patients dans le temps.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Une feature dérivée qui dépend de `maintenant()` n'est pas stable : sa valeur et
toute analyse qui en découle bougent avec la date d'exécution. Sur des données
figées ou synthétiques, préférer les grandeurs intrinsèques (dates brutes,
durées mesurées dans le jeu) aux durées relatives à l'instant présent, ou
assumer et documenter la date de référence comme un paramètre.

**Piège à éviter**
Calculer une ancienneté « depuis aujourd'hui » sur un extrait de données daté, puis
publier le dashboard : les nombres affichés vieillissent silencieusement et
finissent par ne plus correspondre à rien.

---

## Étape 4 — Conception du dashboard

Six visualisations définies avant toute implémentation. Public visé : diététicien·ne
ou responsable de service voulant lire les tendances d'une patientèle de 2500 dossiers
(profils, régimes, évolution du poids, indicateurs à risque). Cette étape ne produit
pas de code ; elle fixe pour chaque vue la question métier, le type de graphique, le
traitement des valeurs imputées (règle 2.4) et la parade au risque de faux lien.

### 4.1 — Principe transversal : pas de croisement numérique × numérique

**Décision prise**
Le dashboard n'utilise que des distributions univariées et des comparaisons
catégorielle × numérique (barres, barres empilées, box plots). Aucun nuage de points
entre deux variables numériques, aucune droite de tendance ajustée sur un couple
numérique. Toute barre de proportion affiche l'effectif de son groupe et garde un
ordre de catégories fixe (jamais trié par la valeur affichée).

**Pourquoi**
L'EDA a établi des corrélations paire-à-paire quasi nulles entre toutes les variables
numériques (|r| ≤ 0,03), `weight_change_pct` en tête. Un nuage de points invite l'œil
à chercher une pente ; sur des variables non corrélées, le lecteur *trouvera* une
structure qui n'existe pas (regroupements visuels, points « extrêmes » interprétés
comme significatifs). Trier des barres par leur taux transforme un écart de bruit en
classement apparent.

**Seule exception assumée** : `weight_change_pct` × `diet_type` (VIZ 4). C'est un
croisement catégoriel × numérique, testé (Kruskal-Wallis p ≈ 3 × 10⁻³⁴), avec un
effet cliniquement attendu (le régime hypocalorique fait perdre du poids). Il est
présenté comme une comparaison de groupes, pas comme une relation continue.

**Alternatives envisagées**
- *Autoriser les scatters avec un avertissement écrit* — écarté : l'avertissement ne
  neutralise pas la lecture visuelle ; la forme du graphe raconte plus fort que sa
  légende.
- *Ajouter des droites de régression « pour référence »* — écarté : une pente tracée
  sur un r ≈ 0 est une invitation directe au contresens.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL, attendu au brief]**
Le choix du type de graphique encode une hypothèse sur la structure des données. Un
scatter affirme « il peut y avoir une relation ici » ; ne l'employer que quand l'EDA
a montré qu'une relation existe. Sur des variables non corrélées, préférer les
distributions séparées et les comparaisons de groupes, qui ne suggèrent rien au-delà
de ce qui est mesuré. Corollaire (distribution brute vs comparative) : montrer une
distribution normalisée / centrée sur une cible plutôt que brute change ce qu'un
lecteur non technique peut mal interpréter — cf. VIZ 3 et VIZ 5, cadrées autour d'une
ligne de référence.

**Piège à éviter**
Le « juste au cas où » : ajouter un scatter exploratoire dans un dashboard destiné à
des non-analystes parce qu'il est facile à produire. Ce qui est un outil d'EDA pour
un analyste est un piège à interprétation pour un lecteur métier.

### 4.2 — VIZ 1 : Vue d'ensemble de la patientèle

**Question métier** : comment se compose ma file active — statut pondéral, régimes
prescrits, pathologies — et combien de dossiers sont prioritaires ?

**Décision prise**
Un bandeau de KPI (N patients, âge médian, part d'IMC hors norme, part
`risk_screen_score` ≥ 2) suivi de trois barres horizontales : `bmi_category`,
`diet_type`, `condition`.

**Type et pourquoi**
Barres et non camemberts : plusieurs catégories dont il faut comparer et classer les
effectifs ; la barre donne la longueur comparable, le camembert oblige à comparer des
angles. `bmi_category` reste en ordre clinique (insuffisance pondérale → obésité),
`diet_type` et `condition` en ordre fixe (effectif décroissant figé une fois pour
toutes, pas recalculé après filtrage). KPI en chiffres bruts : ce sont des totaux, pas
des séries à comparer.

**Règle 2.4** : aucune variable imputée. `condition = "Non renseigné"` est une barre
distincte, jamais fondue dans « Aucune ».

**Risque de faux lien** : nul, tout est univarié.

### 4.3 — VIZ 2 : Triage — score de risque et drapeaux

**Question métier** : quels dossiers revoir en priorité, et quel signal les fait
remonter ?

**Décision prise**
Trois éléments : (a) barres de la distribution de `risk_screen_score` (0→4), scindées
complet / incomplet ; (b) barres horizontales de la fréquence de chaque `flag_*` ;
(c) barres empilées horizontales de la composition du score par `diet_type`.

**Type et pourquoi**
(a) et (b) sont des décomptes → barres. (c) est une décomposition part-à-tout (de quoi
est fait le risque dans chaque groupe de régime) → barres empilées horizontales
(labels de régime longs). L'empilement montre une composition, pas une corrélation.

**Règle 2.4** : `risk_screen_score` est déjà conforme (drapeaux levés sur donnée
observée uniquement). La distribution (a) affiche la ventilation complet /
`risk_screen_incomplete` ; l'interrupteur global « exclure les valeurs imputées /
scores incomplets » retire les scores incomplets des KPI et de la vue (c). Effectifs
affichés.

**Risque de faux lien** : le drapeau `flag_sodium_high_cardiorenal` n'est défini que
pour les pathologies cardio-rénales ; tout écart entre pathologies sur ce drapeau est
**mécanique**, pas empirique. Les drapeaux protéine / poids ne dépendent pas du
régime : leur variation entre régimes reflète la composition des groupes. Annotation
explicite sur (c) : « seuils de drapeaux indépendants du régime, sauf le sodium via la
pathologie ». Le score n'est jamais présenté comme la découverte d'un lien
régime ↔ risque, seulement comme un décompte de critères-seuils.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Quand un indicateur composite est en partie construit à partir d'une variable de
segmentation, tout graphe qui croise l'indicateur avec cette variable contient une
part de circularité. La signaler explicitement, ou choisir une segmentation
indépendante de la définition de l'indicateur.

### 4.4 — VIZ 3 : Apports observés vs cible thérapeutique, par régime

**Question métier** : les apports observés collent-ils à l'objectif du régime ? Le
sodium des patients « Sans sel » est-il réellement bas ? Les protéines des
« Hyperprotéiné » réellement hautes ?

**Décision prise**
Deux box plots : `daily_sodium_mg` par `diet_type` et `protein_per_kg` par
`diet_type`, chacun avec une ligne de référence (≈ 2300 mg/j ; 0,8 g/kg/j).

**Type et pourquoi**
Box plot : montre médiane, dispersion et queue par groupe — ce qu'il faut pour juger
« ce groupe est-il là où il devrait être ». Ordre des régimes fixe, boîtes non triées
par médiane. Le graphe est cadré autour de l'**écart à la ligne de cible**, pas autour
des différences entre boîtes.

**Règle 2.4** : `daily_sodium_mg` (154 imputés) et `daily_protein_g` (104, via
`protein_per_kg`) → box plots sur valeurs observées uniquement, n par boîte affiché.
L'interrupteur global peut réintégrer les imputés à titre de comparaison, avec un
avertissement sur la déformation.

**Risque de faux lien** : l'EDA montre que sodium et protéines **ne diffèrent pas par
régime** (Kruskal p = 0,31 / 0,56). Les boîtes vont se superposer presque
parfaitement — c'est le constat à lire (« les libellés de régime ne se traduisent pas
dans les apports »), pas du bruit à sur-interpréter. Annotation : « distributions
attendues comme largement superposées ; lire l'écart à la cible, pas l'écart entre
régimes ».

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Montrer une distribution **par rapport à une référence** (ligne de cible) plutôt que
brute oriente la lecture vers la bonne question et empêche la sur-lecture de petites
différences entre groupes. Une distribution brute laisse le lecteur non technique
inventer un classement ; la même distribution avec un seuil de référence répond à
« qui est au-dessus / en dessous de la cible ».

### 4.5 — VIZ 4 : Évolution du poids par type de régime

**Question métier** : les patients sous régime hypocalorique perdent-ils effectivement
du poids ? Comment se compare l'évolution entre régimes ?

**Décision prise**
Box plot de `weight_change_pct` par `diet_type`, ligne de référence à 0 %.

**Type et pourquoi**
C'est le seul croisement que les données portent (Kruskal p ≈ 3 × 10⁻³⁴). Box plot
pour montrer la distribution complète par groupe, pas seulement la moyenne. Polarité
(perte / prise) lue par la position des boîtes vis-à-vis de la ligne 0.

**Règle 2.4** : `weight_change_pct` est la colonne la plus imputée (225, 9 %) et
l'imputation était **stratifiée par `diet_type`** — les valeurs imputées tombent
exactement sur la médiane de chaque régime, ce qui resserrerait artificiellement les
boîtes et **exagérerait** l'écart entre groupes. Exclusion stricte des imputés par
défaut, n par groupe affiché. L'interrupteur permet la comparaison avec / sans imputés
à titre démonstratif.

**Risque de faux lien** : `weight_change_pct` n'est corrélé à aucune variable
numérique → aucun scatter contre calories, visites, âge ou durée de suivi. Croisement
limité à `diet_type` (et, en option, `condition`), catégoriels.

**Piège à éviter**
Imputer une variable en stratifiant par un facteur, puis présenter une comparaison
entre les niveaux de ce même facteur sans retirer les valeurs imputées : la
stratification de l'imputation fabrique alors une partie de l'effet qu'on croit
observer.

### 4.6 — VIZ 5 : Adéquation protéique de la patientèle

**Question métier** : quelle part de la file est sous l'apport protéique de référence
(0,8 g/kg), et est-ce concentré sur certains profils (âge, pathologie) ?

**Décision prise**
(a) Histogramme de `protein_per_kg` avec ligne à 0,8 g/kg ; (b) barres du taux sous
0,8 g/kg par tranche d'âge, avec bascule par `condition`.

**Type et pourquoi**
Histogramme pour la forme de la distribution ; barres de proportion pour localiser une
éventuelle concentration. Tranches d'âge en ordre naturel (18-34 → 75-84), jamais
triées par le taux.

**Règle 2.4** : `protein_per_kg_imputed` (104) → histogramme sur observés uniquement ;
le taux (b) est un agrégat calculé sur les observés, dénominateur = n observé par
groupe, affiché.

**Risque de faux lien** : `protein_per_kg` vs âge, corrélation ≈ −0,01. Les barres par
tranche d'âge seront quasi plates (~27 % partout). Ordre naturel des tranches (pas de
tri par taux) pour ne pas suggérer un gradient ; annotation « pas de concentration par
âge » si c'est le constat.

### 4.7 — VIZ 6 : Flux d'admissions dans le temps (version allégée)

**Question métier** : comment évolue le volume d'entrées au service sur la période
couverte ?

**Décision prise**
Barres simples des admissions par mois, sans segmentation par pathologie, sans droite
de tendance ni moyenne mobile.

**Vérification de stationnarité (faite avant de décider)** : sur les 18 mois couverts
(janvier 2025 – juin 2026), moyenne 139 admissions/mois, écart-type 14, coefficient de
variation 0,10, étendue 109–164. Ajustement à une loi uniforme non rejeté
(χ² p ≈ 0,05) ; régression linéaire du volume mensuel non significative
(pente ≈ +1,2/mois, p ≈ 0,16) ; pas de motif saisonnier visible. **Le flux est
stationnaire** sur la période.

**Type et pourquoi**
Barres mensuelles brutes. Pas de lissage : une moyenne mobile ou une tendance tracée
sur un flux stationnaire suggérerait une dynamique inexistante. Pas de segmentation
par `condition` : à ajouter seulement si une vraie variation du flux total apparaît et
demande à être décomposée — ce n'est pas le cas ici.

**Règle 2.4** : aucune variable imputée ; `admission_date` utilisée brute (décision
3.5).

**Risque de faux lien** : le principal risque est de suggérer une tendance ; neutralisé
en s'en tenant aux barres brutes et en annotant « flux stable sur la période, pas de
tendance significative ».

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Avant d'ajouter une tendance ou un lissage à une série temporelle, tester si la série
varie réellement. Un lissage appliqué par réflexe sur un signal plat crée une histoire
là où il n'y en a pas. La segmentation d'une série se justifie quand la série agrégée
bouge et qu'on cherche *pourquoi* — pas par défaut.

### 4.8 — Filtres interactifs

**Décision prise**
Cinq contrôles, dans une barre latérale unique s'appliquant à toutes les vues :
`diet_type` (multi-sélection), `condition` (multi-sélection), tranche d'âge (bandes
18-34 / 35-49 / 50-64 / 65-74 / 75-84), `bmi_category` (multi-sélection ordonnée),
et un interrupteur « exclure les valeurs imputées / scores incomplets ». Les filtres
se composent en ET ; une alerte s'affiche si un groupe filtré passe sous ~30 patients.

**Pourquoi ceux-là**
- `diet_type` et `condition` : axes de travail d'un service de diététique ; les cibles
  thérapeutiques dépendent de la pathologie, l'organisation du suivi dépend du régime.
- tranche d'âge : les besoins nutritionnels varient avec l'âge ; en bandes cliniques
  conventionnelles plutôt qu'un curseur libre (des plages arbitraires produisent des
  effectifs bruités et non comparables d'un utilisateur à l'autre).
- `bmi_category` : segmentation clinique centrale, catégorie ordonnée déjà construite
  à l'étape 3.
- interrupteur imputés : rend la règle 2.4 actionnable dans l'interface plutôt que
  figée dans le code.

**Alternatives / filtres écartés**
- *Tranche de `follow_up_weeks`* — écarté : distribution uniforme, non reliée à quoi
  que ce soit (décision 3.4) ; filtrer par elle ne segmente rien de lisible.
- *Curseurs numériques (calories, sodium, IMC continu)* — écartés : trop granulaires
  pour un tableau de tendances ; les box plots montrent déjà ces distributions, et un
  curseur invite à découper l'échantillon jusqu'à des effectifs ininterprétables.
- *Filtre `gender`* — écarté : répartition ≈ 50/50 et aucune des six questions métier
  ne s'appuie sur le genre. À rouvrir seulement si une question genrée émerge.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Un filtre n'a de valeur que s'il sépare des sous-populations qui diffèrent sur ce que
le dashboard montre. Proposer un filtre sur une variable sans structure (ici la durée
de suivi) donne à l'utilisateur l'illusion d'un axe d'analyse pertinent et multiplie
les combinaisons à effectif faible. Choisir les filtres d'après les questions métier
et la structure observée, pas d'après la liste des colonnes disponibles.

**Piège à éviter**
Laisser les filtres se composer jusqu'à des effectifs où un box plot ou une proportion
n'a plus de sens, sans le signaler. D'où l'alerte sous ~30 patients par groupe.

---

## Étape 5 — Construction du dashboard Streamlit

Fichier : `app.py` (lancé par `streamlit run app.py`), lisant
`data/patients_nutrition_features.csv`. `requirements.txt` fige les versions pour le
déploiement. La conception de l'étape 4 est appliquée telle quelle ; cette section ne
documente que les choix d'implémentation non tranchés à l'étape 4.

### 5.1 — Plotly comme bibliothèque de graphiques

**Décision prise**
Graphiques en Plotly (`plotly.graph_objects`), rendus via `st.plotly_chart`.

**Pourquoi**
Les vues définies à l'étape 4 demandent des box plots par groupe, des barres
empilées et groupées, des lignes de référence et un ordre de catégories imposé
(jamais trié par valeur). Plotly couvre les quatre directement : `add_box`,
`barmode`, `add_hline`/`add_vline`, `categoryorder="array"` + `categoryarray`. Le
survol par marque est fourni sans code supplémentaire.

**Alternatives envisagées**
- *Altair* — écarté : box plots moins directs, et rendu moins courant sur Streamlit
  Community Cloud (cible de l'étape 6).
- *Matplotlib* — écarté : pas d'interactivité ni de tooltip, or l'accès à la valeur
  au survol fait partie des exigences d'accessibilité retenues.
- *Graphiques natifs Streamlit* (`st.bar_chart`, etc.) — écartés : pas de box plot,
  contrôle insuffisant de l'ordre des catégories et des lignes de référence.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Choisir la bibliothèque de visualisation d'après la liste des primitives réellement
requises par les vues déjà spécifiées, pas d'après la familiarité. Spécifier les
vues avant l'outil (étape 4 avant étape 5) rend ce choix mécanique.

### 5.2 — Palette catégorielle fixe, validée pour le daltonisme

**Décision prise**
Palette de 8 teintes dans un ordre fixe (bleu, orange, aqua, jaune, magenta, vert,
violet, rouge), issue d'une méthode de data-viz où cet ordre est validé pour la
séparation sous déficience de vision des couleurs. Teinte assignée par entité, jamais
recyclée ni recalculée au filtrage. Les barres univariées (comptages, histogrammes,
flux mensuel) utilisent une seule teinte (slot 1), pas un dégradé.

**Pourquoi**
Un dégradé sur des catégories nominales (un régime plus foncé parce que plus
d'effectif) double-encode la longueur de barre dans la couleur et brûle le seul canal
libre. Une couleur par série, fixée à l'entité, garantit qu'un filtre qui change le
nombre de séries ne repeint pas les survivantes — un lecteur qui a associé une
couleur à un drapeau la retrouve.

**Piège à éviter**
Laisser la bibliothèque cycler automatiquement les couleurs au-delà de la palette, ou
trier les barres par valeur en laissant la couleur suivre le rang : les deux cassent
l'association couleur ↔ signification.

### 5.3 — Onglets, jumeaux tabulaires, thème clair

**Décisions prises**
- Six vues réparties en onglets (`st.tabs`) plutôt qu'un long défilement : chaque
  question métier occupe un espace dédié, la barre de filtres latérale s'applique à
  toutes.
- Sous chaque graphique, un `st.expander("Voir les données")` affiche le tableau
  agrégé correspondant — jumeau tabulaire exigé pour l'accessibilité (toute valeur
  lisible autrement que par la couleur ou le survol).
- Thème clair assumé (surface claire, encre sombre) : les graphiques ne suivent pas
  le mode sombre éventuel de Streamlit. **Limite** à consigner dans le README final.

**Bonne pratique générale illustrée** — **[PRINCIPE GÉNÉRAL]**
Tout graphique a un jumeau tabulaire. La couleur et l'interaction enrichissent ;
elles ne doivent jamais être le seul moyen d'atteindre une valeur.

### 5.4 — Sémantique de l'interrupteur « exclure les valeurs imputées »

**Décision prise**
Interrupteur unique dans la barre latérale, **activé par défaut**.
- Activé : VIZ 3, 4, 5 tracent les distributions sur les seules valeurs observées
  (`~<col>_imputed`) ; VIZ 2 exclut `risk_screen_incomplete` des KPI et de la vue
  « taux par régime ». Un `caption` indique le nombre de lignes retirées.
- Désactivé : les lignes imputées sont réintégrées, avec un `caption`
  d'avertissement sur la déformation (pic à la médiane, écart entre régimes exagéré
  pour VIZ 4 du fait de l'imputation stratifiée).
- VIZ 1 et VIZ 6 : aucun effet (pas de colonne imputée en jeu).

**Pourquoi**
La règle 2.4 impose des distributions sur valeurs observées ; l'état par défaut la
respecte sans action de l'utilisateur. La position « désactivé » existe pour montrer
explicitement l'effet de l'imputation, pas comme mode d'analyse recommandé.

### 5.5 — Constantes de seuil fixées dans le code

| Constante | Valeur | Justification |
|---|---|---|
| Cible sodium (ligne de référence VIZ 3) | 2300 mg/j | repère OMS population générale ; une ligne unique lisible plutôt qu'une cible différente par pathologie |
| Référence protéique (VIZ 3, VIZ 5, drapeau) | 0,8 g/kg/j | apport de référence adulte OMS/EFSA |
| Effectif de groupe « faible » | 30 | en deçà, un box plot ou une proportion par groupe est signalé comme à lire avec prudence |
| Sélection filtrée « réduite » | 50 | en deçà, avertissement global sur la lecture des distributions |

**Piège à éviter**
Enfouir ces seuils comme nombres nus dans le code des vues. Regroupés en constantes
nommées en tête de fichier, ils sont révisables sans relire toute la logique, et le
`DECISIONS.md` peut les justifier un par un.

---
