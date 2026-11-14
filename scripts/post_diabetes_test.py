from api_client import post_json
from samples import DIABETES_EXTREME

print(post_json("/predict/diabetes", DIABETES_EXTREME))
