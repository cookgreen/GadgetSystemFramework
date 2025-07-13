cd gsf_framework/
python -m build

pip uninstall gsf-framework -y
pip install dist/gsf_framework-0.1.0-py3-none-any.whl

cd..
gsf-manager
