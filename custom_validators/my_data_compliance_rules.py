import re

from nautobot.apps.models import ComplianceError, DataComplianceRule


class ValidateContacts(DataComplianceRule):
    model = "extras.contact"  # Ex: 'dcim.device'
    enforce = False  # True/False enforce flag

    def audit_name_first_and_last(self):
        # Your logic to determine if this function has succeeded or failed
        if len(self.context["object"].name.split()) <= 1:
            raise ComplianceError({"Name": "Contact must be first and last."})

    def audit(self):
        messages = {}
        for fn in [self.audit_name_first_and_last]:  # Add audit functions here
            try:
                fn()
            except ComplianceError as ex:
                messages.update(ex.message_dict)
        if messages:
            raise ComplianceError(messages)


class DeviceDataComplianceRules(DataComplianceRule):
    model = "dcim.device"
    enforce = True

    # Checks if a device name contains any special characters other than a dash (-), underscore (_), or period (.) using regex
    def audit_device_name_chars(self):
        if not re.match("^[a-zA-Z0-9._-]+$", self.context["object"].name):
            raise ComplianceError(
                {"name": "Device name contains unallowed special characters."}
            )

    def audit(self):
        messages = {}
        for fn in [self.audit_device_name_chars]:
            try:
                fn()
            except ComplianceError as ex:
                messages.update(ex.message_dict)
        if messages:
            raise ComplianceError(messages)


class SerialNotEmptyActiveStatus(DataComplianceRule):
    model = "dcim.device"
    enforce = True

    def audit_serial_not_empty(self):
        obj = self.context["object"]
        if not obj.serial and obj.status.name == "Active":
            raise ComplianceError(
                {
                    "name": "Devices with status of Active MUST have a serial number assigned."
                }
            )

    def audit(self):
        messages = {}
        for fn in [self.audit_serial_not_empty]:
            try:
                fn()
            except ComplianceError as ex:
                messages.update(ex.message_dict)
        if messages:
            raise ComplianceError(messages)


class VlanAssignedOneLocation(DataComplianceRule):
    model = "ipam.vlan"
    enforce = True

    def vlan_must_have_one_location(self):
        # Odd fields on vlans 'location', 'location_assignments', 'locations'
        print(f"Validation Object: {type(self.context['object'])}")
        print(f"Location: {self.context['object'].location}")
        print(f"Locations: {self.context['object'].locations}")
        print(f"Location Assignments: {self.context['object'].location_assignments}")
        print(self.context["object"].location_assignments)
        print(self.context["object"].location_assignments.count())
        # ['DoesNotExist', 'Meta', 'MultipleObjectsReturned', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__firstlineno__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__static_attributes__', '__str__', '__subclasshook__', '__weakref__', '_check_column_name_clashes', '_check_composite_pk', '_check_constraints', '_check_db_table_comment', '_check_default_pk', '_check_field_name_clashes', '_check_fields', '_check_id_field', '_check_indexes', '_check_local_fields', '_check_long_column_names', '_check_m2m_through_same_relationship', '_check_managers', '_check_model', '_check_model_name_db_lookup_clashes', '_check_ordering', '_check_property_name_related_field_accessor_clashes', '_check_single_primary_key', '_check_swappable', '_check_unique_together', '_content_type', '_content_type_cache_key', '_content_type_cached', '_custom_field_data', '_do_insert', '_do_update', '_generate_field_lookups_from_natural_key_field_names', '_get_FIELD_display', '_get_expr_references', '_get_field_expression_map', '_get_next_or_previous_by_FIELD', '_get_next_or_previous_in_order', '_get_pk_val', '_get_unique_checks', '_is_pk_set', '_location', '_meta', '_parse_save_params', '_perform_date_checks', '_perform_unique_checks', '_prepare_related_fields_for_save', '_save_parents', '_save_table', '_set_pk_val', '_state', '_validate_force_insert', 'adelete', 'arefresh_from_db', 'asave', 'associated_contacts', 'associated_data_compliance', 'associated_object_metadata', 'associations', 'cf', 'check', 'clean', 'clean_fields', 'clone_fields', 'composite_key', 'controller_managed_device_group_wireless_network_assignments', 'created', 'csv_natural_key_field_lookups', 'custom_field_data', 'date_error_message', 'delete', 'description', 'destination_for_associations', 'display', 'dynamic_groups', 'dynamic_groups_cached', 'dynamic_groups_list', 'dynamic_groups_list_cached', 'from_db', 'full_clean', 'get_absolute_url', 'get_changelog_url', 'get_computed_field', 'get_computed_fields', 'get_computed_fields_grouping', 'get_computed_fields_grouping_advanced', 'get_computed_fields_grouping_basic', 'get_constraints', 'get_custom_field_groupings', 'get_custom_field_groupings_advanced', 'get_custom_field_groupings_basic', 'get_custom_fields', 'get_custom_fields_advanced', 'get_custom_fields_basic', 'get_data_compliance_url', 'get_deferred_fields', 'get_dynamic_groups_url', 'get_interfaces', 'get_notes_url', 'get_relationships', 'get_relationships_data', 'get_relationships_data_advanced_fields', 'get_relationships_data_basic_fields', 'get_relationships_with_related_objects', 'get_status_color', 'get_status_display', 'get_vminterfaces', 'has_computed_fields', 'has_computed_fields_advanced', 'has_computed_fields_basic', 'id', 'interfaces', 'interfaces_as_tagged', 'interfaces_as_untagged', 'is_approval_workflow_model', 'is_cloud_resource_type_model', 'is_contact_associable_model', 'is_data_compliance_model', 'is_dynamic_group_associable_model', 'is_metadata_associable_model', 'is_saved_view_model', 'last_updated', 'location', 'location_assignments', 'locations', 'name', 'natural_key', 'natural_key_args_to_kwargs', 'natural_key_field_lookups', 'natural_key_field_names', 'natural_slug', 'notes', 'objects', 'page_title', 'pk', 'prefixes', 'prepare_database_save', 'present_in_database', 'refresh_from_db', 'required_related_objects_errors', 'role', 'role_id', 'save', 'save_base', 'serializable_value', 'source_for_associations', 'static_group_association_set', 'status', 'status_id', 'tagged_items', 'tags', 'tenant', 'tenant_id', 'to_objectchange', 'unique_error_message', 'validate_constraints', 'validate_unique', 'validated_save', 'vid', 'vlan_group', 'vlan_group_id', 'vminterfaces', 'vminterfaces_as_tagged', 'vminterfaces_as_untagged', 'vpn_terminations']
        if (
            not self.context["object"].location_assignments
            or self.context["object"].location_assignments.count() != 1
        ):
            raise ComplianceError(
                {"locations": "VLANs must assign one and only one location."}
            )

    def audit(self):
        messages = {}
        for fn in [self.vlan_must_have_one_location]:
            try:
                fn()
            except ComplianceError as ex:
                messages.update(ex.message_dict)
        if messages:
            raise ComplianceError(messages)


class InterfaceVlansMatchLocation(DataComplianceRule):
    model = "dcim.interface"
    enforce = True

    def vlan_and_device_location_match(self):
        if not self.context["object"].mode:
            return
        device_location = self.context["object"].device.location.name
        untagged = self.context["object"].untagged_vlan  # Single vlan object
        print(untagged)
        print(type(untagged))
        if untagged and device_location != untagged.location.name:
            raise ComplianceError(
                {"untagged_vlan": "VLAN isn't the same as the devices location."}
            )
        tagged = self.context["object"].tagged_vlans.all()  # vlan queryset
        if tagged:
            for vlan_location in tagged:
                if device_location != vlan_location.location.name:
                    raise ComplianceError(
                        {"tagged_vlans": "VLAN isn't the same as the devices location."}
                    )

    def audit(self):
        messages = {}
        for fn in [self.vlan_and_device_location_match]:
            try:
                fn()
            except ComplianceError as ex:
                messages.update(ex.message_dict)
        if messages:
            raise ComplianceError(messages)
