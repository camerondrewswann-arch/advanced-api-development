name: Mechanic Shop API CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  build:
    name: Build
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt
          python -m pip check

      - name: Check Python syntax
        run: python -m compileall -q app tests flask_app.py run.py seed.py config.py

  test:
    name: Test
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt

      - name: Run test suite
        env:
          APP_ENV: testing
        run: python -m pytest -q

  deploy:
    name: Deploy to Render
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render deployment
        env:
          SERVICE_ID: ${{ secrets.SERVICE_ID }}
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
          COMMIT_SHA: ${{ github.sha }}
        run: |
          test -n "$SERVICE_ID" || (echo "Missing SERVICE_ID secret" && exit 1)
          test -n "$RENDER_API_KEY" || (echo "Missing RENDER_API_KEY secret" && exit 1)

          curl --fail-with-body --show-error --silent \
            --request POST \
            --url "https://api.render.com/v1/services/${SERVICE_ID}/deploys" \
            --header "Authorization: Bearer ${RENDER_API_KEY}" \
            --header "Accept: application/json" \
            --header "Content-Type: application/json" \
            --data "{\"commitId\":\"${COMMIT_SHA}\"}"
