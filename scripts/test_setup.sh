#!/bin/bash
# Test script to verify the publications auto-update setup

set -e

echo "================================"
echo "Testing Publications Setup"
echo "================================"
echo ""

# Check if required files exist
echo "✓ Checking file structure..."

if [ ! -f "scripts/fetch_publications.py" ]; then
    echo "✗ Error: scripts/fetch_publications.py not found"
    exit 1
fi

if [ ! -f "scripts/requirements.txt" ]; then
    echo "✗ Error: scripts/requirements.txt not found"
    exit 1
fi

if [ ! -f ".github/workflows/update-publications.yml" ]; then
    echo "✗ Error: .github/workflows/update-publications.yml not found"
    exit 1
fi

if [ ! -f "_data/publications.yml" ]; then
    echo "✗ Error: _data/publications.yml not found"
    exit 1
fi

echo "  ✓ All required files exist"
echo ""

# Check Python installation
echo "✓ Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "  ✓ Found $PYTHON_VERSION"
echo ""

# Check if virtual environment exists, if not suggest creating one
echo "✓ Checking Python dependencies..."
if [ ! -d "venv" ]; then
    echo "  ! No virtual environment found. Creating one..."
    python3 -m venv venv
    echo "  ✓ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || . venv/bin/activate

# Install dependencies
echo "  Installing dependencies..."
pip install -q -r scripts/requirements.txt

if [ $? -eq 0 ]; then
    echo "  ✓ Dependencies installed successfully"
else
    echo "✗ Error: Failed to install dependencies"
    exit 1
fi
echo ""

# Check for ADS API key
echo "✓ Checking for ADS API key..."
if [ -z "$ADS_API_KEY" ]; then
    echo "  ! Warning: ADS_API_KEY environment variable not set"
    echo ""
    echo "  To test the script, you need to:"
    echo "  1. Get your API key from: https://ui.adsabs.harvard.edu/user/settings/token"
    echo "  2. Run: export ADS_API_KEY='your-key-here'"
    echo "  3. Run this test script again"
    echo ""
    echo "  For GitHub Actions, add the key as a secret:"
    echo "  Settings → Secrets → Actions → New repository secret"
    echo "  Name: ADS_API_KEY"
    echo ""
else
    echo "  ✓ ADS_API_KEY is set"
    echo ""

    # Try to fetch publications
    echo "✓ Testing publication fetch..."
    cd scripts
    if python3 fetch_publications.py; then
        echo "  ✓ Successfully fetched publications from ADS!"
        cd ..

        # Check if publications.yml was updated
        if [ -f "_data/publications.yml" ]; then
            PUB_COUNT=$(grep -c "^- title:" _data/publications.yml)
            echo "  ✓ Found $PUB_COUNT publications in _data/publications.yml"
        fi
    else
        echo "✗ Error: Failed to fetch publications"
        cd ..
        exit 1
    fi
    echo ""
fi

# Validate YAML syntax
echo "✓ Validating YAML syntax..."
python3 -c "
import yaml
import sys
try:
    with open('_data/publications.yml', 'r') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        print('✗ Error: publications.yml should contain a list')
        sys.exit(1)
    print(f'  ✓ Valid YAML with {len(data)} publications')
except Exception as e:
    print(f'✗ Error: Invalid YAML: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi
echo ""

# Check Jekyll files
echo "✓ Checking Jekyll configuration..."
if [ -f "_config.yml" ]; then
    echo "  ✓ _config.yml exists"
fi

if [ -f "_layouts/home.html" ]; then
    # Check if home.html uses the publications data
    if grep -q "site.data.publications" "_layouts/home.html"; then
        echo "  ✓ home.html is configured to use publications data"
    else
        echo "  ✗ Warning: home.html may not be using publications data"
    fi
fi
echo ""

echo "================================"
echo "✓ Setup verification complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Add ADS_API_KEY to GitHub repository secrets"
echo "2. Commit and push the changes"
echo "3. Enable GitHub Actions in your repository"
echo "4. Manually trigger the workflow or wait for weekly run"
echo ""
echo "To manually update publications locally:"
echo "  export ADS_API_KEY='your-key-here'"
echo "  python3 scripts/fetch_publications.py"
echo ""
