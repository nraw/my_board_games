run:
	python3 main.py

install:
	pip install -r requirements.txt

move_data:
	cp -R data/*json 11ty_site/_data/.
