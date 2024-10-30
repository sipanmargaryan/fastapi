from alembic.operations import ops
from alembic.script import ScriptDirectory


def process_revision_directives(context, revision, directives):
    migration_script = directives[0]
    increase_migration_sequence_by_one(context, migration_script)
    filter_drop_indexes(migration_script)


def increase_migration_sequence_by_one(context, script):
    head_revision = ScriptDirectory.from_config(context.config).get_current_head()

    if head_revision is None:
        new_rev_id = 1
    else:
        last_rev_id = int(head_revision.lstrip("0"))
        new_rev_id = last_rev_id + 1
    script.rev_id = f"{new_rev_id:05}"


def filter_drop_indexes(script):
    for directive in (script.upgrade_ops, script.downgrade_ops):
        tables_dropped = set()
        for op in directive.ops:
            if isinstance(op, ops.DropTableOp):
                tables_dropped.add((op.table_name, op.schema))

        directive.ops = list(_filter_drop_indexes(directive.ops, tables_dropped))


def _filter_drop_indexes(directives, tables_dropped):
    for directive in directives:
        if (
            isinstance(directive, ops.ModifyTableOps)
            and (directive.table_name, directive.schema) in tables_dropped
        ):
            directive.ops = list(_filter_drop_indexes(directive.ops, tables_dropped))
            if not directive.ops:
                continue
        elif (
            isinstance(directive, ops.DropIndexOp)
            and (directive.table_name, directive.schema) in tables_dropped
        ):
            continue

        yield directive
