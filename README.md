#  Nettoyage et transformation de données télécom

##  Objectif

Ce projet a pour objectif de nettoyer et transformer des données télécom brutes afin de les rendre exploitables pour l’analyse et les traitements Big Data.

##  Contexte

Les données télécom sont souvent :
- volumineuses  
- bruitées  
- incohérentes  

Avant toute analyse ou modélisation, il est nécessaire de passer par une phase de nettoyage et de transformation.

## Problématique

Comment transformer des données brutes en un format optimisé, propre et exploitable pour l’analyse ?

## Technologies utilisées

- Python  
- Pandas  
- Numpy 

## Méthodologie

1. Chargement des données CSV  
2. Nettoyage :
   - suppression des valeurs nulles  
   - correction des types  
   - suppression des doublons  
3. Transformation :
   - normalisation des données  
   - conversion vers format Parquet  
4. Compression :
   - utilisation de Snappy  

---

## 📊 Résultats

- Réduction de la taille des données  
- Amélioration de la qualité des données  
- Format optimisé pour le traitement Big Data  
- Données prêtes pour analyse ou machine learning  

---

## ▶️ Exécution

```bash
# Installation des dépendances
pip install -r requirements.txt

# Lancement du script
python main.py
