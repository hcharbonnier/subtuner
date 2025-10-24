# Préservation des Overlaps lors de l'Optimisation

## Problème Résolu

Auparavant, le système sautait complètement l'optimisation des sous-titres qui se chevauchaient ou qui duraient longtemps. Maintenant, ces sous-titres sont optimisés normalement en autorisant uniquement les chevauchements qui existaient déjà dans le fichier original.

## Solution Implémentée

### 1. Détection des Overlaps Originaux
L'[`OptimizationEngine`](subtuner/optimization/engine.py:162) détecte maintenant tous les chevauchements présents dans les sous-titres originaux avant de lancer l'optimisation.

### 2. Transmission aux Algorithmes
Les overlaps autorisés sont maintenant transmis à **tous** les algorithmes d'optimisation:
- [`DurationAdjuster`](subtuner/optimization/algorithms/duration_adjuster.py:19) - Ajustement de la durée
- [`TemporalRebalancer`](subtuner/optimization/algorithms/rebalancer.py:19) - Rééquilibrage temporel
- [`ConstraintsValidator`](subtuner/optimization/algorithms/validator.py:19) - Validation des contraintes

### 3. Respect des Overlaps dans Chaque Algorithme

#### DurationAdjuster
- Lorsqu'un overlap est autorisé avec le sous-titre suivant, l'algorithme peut étendre la durée jusqu'à la fin du sous-titre suivant
- Cela permet de préserver l'overlap tout en optimisant la durée de lecture

#### TemporalRebalancer
- Saute complètement le rééquilibrage pour les paires de sous-titres ayant un overlap autorisé
- Évite de briser l'overlap intentionnel lors du transfert de temps

#### ConstraintsValidator
- Ne force plus le `min_gap` entre les sous-titres ayant un overlap autorisé
- Préserve l'overlap original tel quel

## Résultat

Les sous-titres avec overlaps originaux peuvent maintenant être optimisés pour améliorer leur lisibilité tout en préservant les chevauchements intentionnels du fichier source.

### Exemple de Test

```python
# Avant (ancien comportement)
Original: Sub 0: 0.0s - 2.5s, Sub 1: 2.0s - 4.0s (overlap 0.5s)
Optimisé: Sub 0: 0.0s - 1.9s, Sub 1: 2.0s - 4.0s (overlap supprimé)

# Après (nouveau comportement)
Original: Sub 0: 0.0s - 2.5s, Sub 1: 2.0s - 4.0s (overlap 0.5s)
Optimisé: Sub 0: 0.0s - 2.5s, Sub 1: 2.0s - 4.0s (overlap préservé 0.5s)
```

## Test de Validation

Un test de validation a été créé dans [`test_overlap_preservation.py`](test_overlap_preservation.py:1) qui confirme que les overlaps originaux sont correctement préservés lors de l'optimisation.