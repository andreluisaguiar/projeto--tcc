"""Registro de algoritmos de Machine Learning disponíveis.

Implementa o padrão Strategy para facilitar a adição de novos modelos
sem modificar o código de treinamento.
"""

from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from src.config import RANDOM_STATE


# ─── Registry de algoritmos ──────────────────────────────────────────────────

ALGORITHM_REGISTRY: dict[str, dict] = {
    "random_forest": {
        "name": "Random Forest",
        "class": RandomForestClassifier,
        "default_params": {
            "n_estimators": 100,
            "class_weight": "balanced",
            "random_state": RANDOM_STATE,
        },
    },
    "naive_bayes": {
        "name": "Naive Bayes",
        "class": MultinomialNB,
        "default_params": {},
    },
    "svm": {
        "name": "SVM",
        "class": SVC,
        "default_params": {
            "probability": True,
            "random_state": RANDOM_STATE,
        },
    },
    "knn": {
        "name": "KNN",
        "class": KNeighborsClassifier,
        "default_params": {},
    },
    "decision_tree": {
        "name": "Decision Tree",
        "class": DecisionTreeClassifier,
        "default_params": {
            "random_state": RANDOM_STATE,
        },
    },
    "xgboost": {
        "name": "XGBoost",
        "class": XGBClassifier,
        "default_params": {
            "use_label_encoder": False,
            "eval_metric": "mlogloss",
            "enable_categorical": False,
            "random_state": RANDOM_STATE,
        },
    },
}


def get_algorithm(name: str, **override_params):
    """Cria uma instância do algoritmo pelo nome.

    Args:
        name: Identificador do algoritmo (chave do registry).
        **override_params: Parâmetros para sobrescrever os defaults.

    Returns:
        Instância do modelo configurado.

    Raises:
        ValueError: Se o algoritmo não for encontrado no registry.
    """
    if name not in ALGORITHM_REGISTRY:
        available = ", ".join(ALGORITHM_REGISTRY.keys())
        raise ValueError(
            f"Algoritmo '{name}' não encontrado. Disponíveis: {available}"
        )

    entry = ALGORITHM_REGISTRY[name]
    params = {**entry["default_params"], **override_params}
    return entry["class"](**params)


def list_algorithms() -> list[str]:
    """Retorna a lista de nomes de algoritmos disponíveis."""
    return list(ALGORITHM_REGISTRY.keys())


def get_display_name(name: str) -> str:
    """Retorna o nome amigável de um algoritmo."""
    return ALGORITHM_REGISTRY[name]["name"]
