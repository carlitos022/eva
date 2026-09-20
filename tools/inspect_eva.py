import os
import sys

ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from brain.memory import MemoryStore
from brain.memory_cortex import MemoryCortex


def print_section(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main():
    store = MemoryStore()
    store.initialize()

    cortex = MemoryCortex(store)
    cortex.initialize()

    print_section("EVA v0.4.0 - ESTADO COGNITIVO PERSISTENTE")

    print("Estadisticas base:")
    for name, count in store.stats().items():
        print(f"  {name:20} {count}")

    print_section("MEMORY CORTEX")
    status = cortex.status()
    print("  engine:", status.get("engine"))
    print("  tree_branches:", status.get("tree_branches"))
    print("  entities:", status.get("entities"))
    print("  tasks:", status.get("tasks"))

    embeddings = status.get("embeddings", {})
    print("  embeddings_enabled:", embeddings.get("enabled"))
    print("  embedding_model:", embeddings.get("model"))
    print("  embeddings_ready:", embeddings.get("ready"))
    if embeddings.get("last_error"):
        print("  embeddings_last_error:", embeddings["last_error"])

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

    print_section("ENTIDADES")
    entities = cortex.list_entities(20)
    if not entities:
        print("  Todavia no hay entidades archivadas.")
    else:
        for entity in entities:
            print(
                f"  #{entity['id']} [{entity['type']}] "
                f"{entity['name']} imp={entity['importance']:.2f}"
            )
            if entity.get("summary"):
                print("     ", entity["summary"])

    print_section("MEMORY TREE")
    tree = cortex.get_memory_tree(20)
    if not tree:
        print("  Arbol vacio.")
    else:
        for branch in tree:
            print(
                f"  {branch['path']} "
                f"({branch['items']} items, "
                f"imp={branch['importance']:.2f})"
            )
            if branch.get("summary"):
                print("     ", branch["summary"][:300])

    print_section("ULTIMAS MEMORIAS")
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
