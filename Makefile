.PHONY: install run test clean

# Instalar dependências
install:
	pip install -r requirements.txt

# Rodar o servidor local
run:
	uvicorn app.main:app --reload

# Rodar testes
test:
	pytest tests/ -v

# Limpar dados temporários
clean:
	rm -rf data/uploads/*
	rm -rf data/results/*
	touch data/uploads/.gitkeep
	touch data/results/.gitkeep
	@echo "Data directories cleaned."
