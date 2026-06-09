"""Launcher local para backup, exportacao e restauracao."""

import argparse

from forja_de_ferro import backup_ops


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Gerencia backup, exportacao e restauracao da Forja de Ferro."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup = subparsers.add_parser("backup", help="Cria um backup SQLite consistente.")
    backup.add_argument("--destino", help="Diretorio de saida.")

    export = subparsers.add_parser("exportar", help="Exporta os dados para JSON.")
    export.add_argument("--destino", help="Diretorio de saida.")

    restore = subparsers.add_parser("restaurar", help="Restaura um backup SQLite.")
    restore.add_argument("arquivo", help="Arquivo .db de backup.")
    restore.add_argument(
        "--confirmar",
        action="store_true",
        help="Confirma a substituicao do banco atual.",
    )
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if args.command == "backup":
        output = backup_ops.criar_backup(args.destino)
        print(f"Backup criado em: {output}")
        return 0
    if args.command == "exportar":
        output = backup_ops.exportar_dados(args.destino)
        print(f"Exportacao criada em: {output}")
        return 0
    if not args.confirmar:
        print("Restauracao cancelada. Use --confirmar para substituir o banco atual.")
        return 2

    output, safety = backup_ops.restaurar_backup(args.arquivo)
    print(f"Banco restaurado em: {output}")
    if safety:
        print(f"Backup de seguranca criado em: {safety}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
