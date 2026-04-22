# Causal Inference Service

## Overview

The **Causal Inference Service** provides an API for performing causal analysis on datasets. It aims to identify potential causal relationships between variables using statistical methods.

---

## API Endpoints

### POST `/infer`

Performs causal inference on the provided data.

- **Request Body:**

  ```json
  {
    "data": {
      "treatment": "variable_name_A",
      "outcome": "variable_name_B",
      "dataframe": [
        {"variable_name_A": 0, "variable_name_B": 10, "confounder": 5},
        {"variable_name_A": 1, "variable_name_B": 25, "confounder": 8}
      ]
    },
    "method": "backdoor.linear_regression"
  }
