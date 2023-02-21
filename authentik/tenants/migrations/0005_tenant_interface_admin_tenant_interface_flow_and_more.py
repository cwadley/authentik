# Generated by Django 4.1.7 on 2023-02-21 14:18

import django.db.models.deletion
from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def migrate_set_default(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    Tenant = apps.get_model("authentik_tenants", "tenant")
    Interface = apps.get_model("authentik_interfaces", "Interface")
    db_alias = schema_editor.connection.alias

    from authentik.blueprints.models import BlueprintInstance
    from authentik.blueprints.v1.importer import Importer
    from authentik.blueprints.v1.tasks import blueprints_discover
    from authentik.interfaces.models import InterfaceType

    # If we don't have any tenants yet, we don't need wait for the default interface blueprint
    if not Tenant.objects.using(db_alias).exists():
        return

    interface_blueprint = BlueprintInstance.objects.filter(path="system/interfaces.yaml").first()
    if not interface_blueprint:
        blueprints_discover.delay().get()
        interface_blueprint = BlueprintInstance.objects.filter(
            path="system/interfaces.yaml"
        ).first()
    if not interface_blueprint:
        raise ValueError("Failed to apply system/interfaces.yaml blueprint")
    Importer(interface_blueprint.retrieve()).apply()

    for tenant in Tenant.objects.using(db_alias).all():
        tenant.interface_admin = Interface.objects.filter(type=InterfaceType.ADMIN).first()
        tenant.interface_user = Interface.objects.filter(type=InterfaceType.USER).first()
        tenant.interface_flow = Interface.objects.filter(type=InterfaceType.FLOW).first()
        tenant.save()


class Migration(migrations.Migration):
    dependencies = [
        ("authentik_interfaces", "0001_initial"),
        ("authentik_tenants", "0004_tenant_flow_device_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="interface_admin",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tenant_admin",
                to="authentik_interfaces.interface",
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="interface_flow",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tenant_flow",
                to="authentik_interfaces.interface",
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="interface_user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tenant_user",
                to="authentik_interfaces.interface",
            ),
        ),
        migrations.RunPython(migrate_set_default),
    ]