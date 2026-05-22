"""Gera o dashboard local de treino em HTML."""

from forja_de_ferro.dashboard import salvar_dashboard


def main():
    caminho = salvar_dashboard()
    print(f"Dashboard de treino gerado em: {caminho}")


if __name__ == "__main__":
    main()
