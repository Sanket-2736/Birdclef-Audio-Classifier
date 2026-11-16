import pickle
import numpy as np

with open(r"models\mlp_artifacts.pkl", "rb") as f:
    a = pickle.load(f)

for key, value in a.items():
    print("\nKEY:", key)
    print("TYPE:", type(value))

    if isinstance(value, np.ndarray):
        print("SHAPE:", value.shape)
        print("DTYPE:", value.dtype)
        print("FIRST VALUES:", value[:10])

    elif isinstance(value, (list, tuple)):
        print("LENGTH:", len(value))
        print("FIRST 10:", repr(value[:10]))

    elif hasattr(value, "__dict__"):
        print("ATTRIBUTES:")
        for attr, val in value.__dict__.items():
            if isinstance(val, np.ndarray):
                print(attr, "shape:", val.shape, "dtype:", val.dtype)
            else:
                print(attr, type(val), repr(val)[:150])

    else:
        print("VALUE:", repr(value)[:500])

