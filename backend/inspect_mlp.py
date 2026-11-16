import pickle
import numpy as np

with open(r"models\mlp_artifacts.pkl", "rb") as f:
    artifacts = pickle.load(f)

print("\n--- PCA ---")
pca = artifacts["pca"]
print("Type:", type(pca))
print("random_state:", repr(getattr(pca, "random_state", None)))
print("Components:", pca.n_components)

print("\n--- Probe models ---")
for i, model in enumerate(artifacts["probe_models"]):
    print(f"\nProbe {i}: {type(model).__name__}")
    print("random_state:", repr(getattr(model, "random_state", None)))

    if hasattr(model, "estimators_"):
        for j, estimator in enumerate(model.estimators_):
            print(
                f"  Estimator {j}: {type(estimator).__name__}, "
                f"random_state={repr(getattr(estimator, 'random_state', None))}"
            )
