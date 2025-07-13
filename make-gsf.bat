cd gsf_framework/
python -m build

pip uninstall gsf-framework
pip install gsf_framework/dist/gsf_framework-0.1.0-py3-none-any.whl
