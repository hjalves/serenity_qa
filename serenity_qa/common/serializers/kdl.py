import json

import ckdl

from django.core.serializers import base


class Serializer(base.Serializer):
    """Serialize a QuerySet to KDL."""

    def start_serialization(self):
        indent = self.options.get("indent") or 0
        self.emitter_options = ckdl.EmitterOptions(indent=indent)

    def end_serialization(self):
        pass

    def start_object(self, obj):
        self._properties = {"model": str(obj._meta)}
        print(self._properties)
        if not self.use_natural_primary_keys or not hasattr(obj, "natural_key"):
            if (obj_pk := obj.pk) is not None:
                self._properties["pk"] = self._serialize(obj_pk)
        self._field_nodes = []

    def end_object(self, obj):
        object_node = ckdl.Node(
            "object", properties=self._properties, children=self._field_nodes
        )
        document = ckdl.Document(object_node)
        self.stream.write(document.dump(self.emitter_options))

    def _value_from_field(self, obj, field):
        value = field.value_from_object(obj)
        if isinstance(value, (type(None), int, float)):
            return value
        if field.get_internal_type() == "JSONField":
            # Improve this
            return json.dumps(value, cls=field.encoder)
        return field.value_to_string(obj)

    def _serialize(self, value):
        if isinstance(value, (type(None), int, float)):
            return value
        return str(value)

    def handle_field(self, obj, field):
        properties = {"name": field.name, "type": field.get_internal_type()}
        args = [self._value_from_field(obj, field)]
        field_node = ckdl.Node("field", args=args, properties=properties)
        self._field_nodes.append(field_node)

    def _start_relational_field(self, field):
        self._field_props = {
            "name": field.name,
            "rel": field.remote_field.__class__.__name__,
            "to": str(field.remote_field.model._meta),
        }

    def handle_fk_field(self, obj, field):
        self._start_relational_field(field)
        related_att = getattr(obj, field.get_attname())
        if related_att is not None:
            if self.use_natural_foreign_keys and hasattr(
                field.remote_field.model, "natural_key"
            ):
                related = getattr(obj, field.name)
                related = [self._serialize(k) for k in related.natural_key()]
                children = [ckdl.Node("natural", args=related)]
                node = ckdl.Node("field", properties=self._field_props, children=children)
            else:
                related_att = self._serialize(related_att)
                node = ckdl.Node("field", related_att, properties=self._field_props)
        else:
            node = ckdl.Node("field", None, properties=self._field_props)
        self._field_nodes.append(node)

    def handle_m2m_field(self, obj, field):
        _children = []
        _args = []

        if field.remote_field.through._meta.auto_created:
            self._start_relational_field(field)
            if self.use_natural_foreign_keys and hasattr(
                field.remote_field.model, "natural_key"
            ):

                def handle_m2m(value):
                    related = [self._serialize(k) for k in value.natural_key()]
                    _children.append(ckdl.Node("natural", args=related))

                def queryset_iterator(obj, field):
                    return getattr(obj, field.name).iterator()

            else:

                def handle_m2m(value):
                    _args.append(self._serialize(value.pk))

                def queryset_iterator(obj, field):
                    return getattr(obj, field.name).only("pk").iterator()

            m2m_iter = getattr(obj, "_prefetched_objects_cache", {}).get(
                field.name,
                queryset_iterator(obj, field),
            )
            for relobj in m2m_iter:
                handle_m2m(relobj)

            node = ckdl.Node(
                "field", args=_args, properties=self._field_props, children=_children
            )
            self._field_nodes.append(node)
