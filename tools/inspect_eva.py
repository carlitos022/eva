import os
import sys

ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from brain.memory import MemoryStore


def print_section(title):
    print()
    print("=" * 68)
    print(title)
    print("=" * 68)


def main():
    store = MemoryStore()
    store.initialize()

    print_section("EVA - ESTADO COGNITIVO PERSISTENTE")

    print("Estadisticas:")
    for name, count in store.stats().items():
        print(f"  {name:18} {count}")

    print_section("IDENTIDAD")
    for item in store.get_identity():
        print(
            f"  {item['subject']}.{item['key']} = "
            f"{item['value']} "
            f"(confianza {item['confidence']:.2f})"
        )

    print_section("RELACION PRINCIPAL")
    relation = store.get_relationship()
    print(
        f"  afinidad={relation['affinity']:.3f}  "
        f"confianza={relation['trust']:.3f}  "
        f"familiaridad={relation['familiarity']:.3f}"
    )
    if relation.get("notes"):
        print("  notas:", relation["notes"])

    print_section("ESTADO EMOCIONAL")
    emotional = store.latest_emotional_state()
    if emotional:
        for key, value in emotional.items():
            print(f"  {key}: {value}")
    else:
        print("  Sin estado guardado.")

    print_section("OBJETIVOS ACTIVOS")
    goals = store.get_active_goals(10)
    if not goals:
        print("  Sin objetivos activos.")
    else:
        for goal in goals:
            print(
                f"  #{goal['id']} {goal['title']} "
                f"(prioridad {goal['priority']:.2f}, "
                f"progreso {goal['progress']:.2f})"
            )

    print_section("ULTIMAS MEMORIAS DE LARGO PLAZO")
    memories = store.list_recent_memories(15)
    if not memories:
        print("  Todavia no hay memorias seleccionadas.")
    else:
        for memory in memories:
            print(
                f"  #{memory['id']} [{memory['type']}] "
                f"imp={memory['importance']:.2f} "
                f"{memory['content']}"
            )


if __name__ == "__main__":
    main()
