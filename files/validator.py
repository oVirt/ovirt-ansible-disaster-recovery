#!/usr/bin/python
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import os.path
import ovirtsdk4 as sdk
import ovirtsdk4.types as types
import shlex
import subprocess
import sys
import yaml


from subprocess import call


class ValidateMappingFile():

    prefix = "[Validate Mapping File] "
    dr_conf_file = "dr.conf"
    def_var_file = "/var/lib/ovirt-ansible-disaster-" \
                   "recovery/mapping_vars.yml"
    cluster_map = 'dr_cluster_mappings'
    domain_map = 'dr_domain_mappings'
    role_map = 'dr_role_mappings'
    aff_group_map = 'dr_affinity_group_mappings'
    aff_label_map = 'dr_affinity_label_mappings'

    def run(self):
        print("%sValidate variable mapping file "
              "for oVirt ansible disaster recovery" % self.prefix)
        yml_var_file = self._get_var_file()
        print("%sVar file: %s" % (self.prefix, yml_var_file))
        python_vars = self._read_var_file(yml_var_file)
        if (not self._validate_duplicate_keys(python_vars) or
                not self._validate_exist_entities(python_vars)):
            print("%s[ERROR] Failed to validate variable mapping file "
                  "for oVirt ansible disaster recovery" % self.prefix)
            exit()
        print("%s[SUCCESS] Finished validating variable mapping file "
              "for oVirt ansible disaster recovery]" % self.prefix)

    def _read_var_file(self, yml_var_file):
        with open(yml_var_file, 'r') as info:
            info_dict = yaml.load(info)
        return info_dict

    def _get_var_file(self):
        # Get default location of the yml var file.
        settings = configparser.ConfigParser()
        settings._interpolation = configparser.ExtendedInterpolation()
        settings.read(self.dr_conf_file)
        var_file = settings.get('validate_vars', 'var_file',
                                vars=DefaultOption(settings,
                                                   'validate_vars',
                                                   site=self.def_var_file))

        # If no default location exists, get the location from the user.
        while (not var_file):
            var_file = raw_input(self.prefix + "var file is not initialized. "
                                 "Please provide the location of the var file "
                                 "(" + self.def_var_file + ")" or def_var_file)
        return var_file

    def _print_duplicate_keys(self, duplicates, keys):
        ret_val = False
        for key in keys:
            if len(duplicates[key]) > 0:
                print("%s[ERROR] Found the following duplicate keys in %s: %s"
                      % (self.prefix, key, list(duplicates[key])))
                ret_val = True
        return ret_val

    def _validate_exist_entities(self, var_file):
        isValid = True
        ovirt_setups = ConnectSDK(var_file, self.prefix)
        isValid = ovirt_setups.validate_primary() and isValid
        isValid = ovirt_setups.validate_secondary() and isValid
        if isValid:
            conn = ovirt_setups.connect_primary()
            isValid = self._validate_cluster_exists(
                conn, var_file, self.cluster_map) and isValid

        self._is_compatible_versions(
            ovirt_setups, var_file.get(
                self.cluster_map))
        return isValid

    def _validate_cluster_exists(self, conn, var_file, key):
        isValid = True
        clusters = []

        dcs_service = conn.system_service().data_centers_service()
        dcs_list = dcs_service.list()
        for dc in dcs_list:
            dc_service = dcs_service.data_center_service(dc.id)
            clusters_service = dc_service.clusters_service()
            attached_clusters_list = clusters_service.list()
            for cluster in attached_clusters_list:
                clusters.append(cluster.name)
        _mapping = var_file.get(key)
        for x in _mapping:
            if x['primary_name'] not in clusters:
                print("%s[ERROR] Entity %s does not exist in %s setup" %
                      (self.prefix, x['primary_name'], "primary"))
                isValid = False
        return isValid

    def _validate_duplicate_keys(self, var_file):
        isValid = True
        clusters = 'clusters'
        domains = 'domains'
        roles = 'roles'
        aff_group = 'aff_group'
        aff_label = 'aff_label'
        network = 'network'
        duplicates = self._get_dups(
            var_file, [
                [clusters, self.cluster_map],
                [domains, self.domain_map],
                [roles, self.role_map],
                [aff_group, self.aff_group_map],
                [aff_label, self.aff_label_map]])
        duplicates[network] = self._get_dup_network(var_file)
        isValid = not self._print_duplicate_keys(
            duplicates, [
                clusters, domains, roles, aff_group, aff_label, network]) and isValid
        return isValid

    def _get_dups(self, var_file, mapping):
        _return_set = set()
        _mapping = var_file.get(mapping)
        _primary = set()
        _secondary = set()
        _return_set.update(set(x['primary_name']
                               for x in _mapping if
                               x['primary_name'] in _primary or
                               _primary.add(x['primary_name'])))
        _return_set.update(set(x['secondary_name']
                               for x in _mapping if
                               x['secondary_name'] in _secondary or
                               _secondary.add(x['secondary_name'])))
        return _return_set

    def _is_compatible_versions(self, var_file, _mapping):
        """ Validate cluster versions """
        # TODO: Add support for compatible cluster versions

    def _get_dups(self, var_file, mappings):
        duplicates = {}
        for mapping in mappings:
            _return_set = set()
            _mapping = var_file.get(mapping[1])
            _primary = set()
            _secondary = set()
            _return_set.update(set(x['primary_name']
                                   for x in _mapping if
                                   x['primary_name'] in _primary or
                                   _primary.add(x['primary_name'])))
            _return_set.update(set(x['secondary_name']
                                   for x in _mapping if
                                   x['secondary_name'] in _secondary or
                                   _secondary.add(x['secondary_name'])))
            duplicates[mapping[0]] = _return_set
        return duplicates

    def _get_dup_network(self, var_file):
        _return_set = set()
        # TODO: Add data center also
        map_name = 'dr_network_mappings'
        _mapping = var_file.get(map_name)

        # Check for profile + network name duplicates in primary
        _primary1 = set()
        key1_a = 'primary_profile_name'
        key1_b = 'primary_network_name'
        for x in _mapping:
            if (x[key1_a] is None or x[key1_b] is None):
                print("%sNetwork '%s' is not initialized in map %s %s"
                      % (self.prefix, x, [key1_a], x[key1_b]))
                exit()
            map_key = x[key1_a] + "_" + x[key1_b]
            if map_key in _primary1:
                _return_set.add(map_key)
            else:
                _primary1.add(map_key)

        # Check for profile + network name duplicates in secondary
        _secondary1 = set()
        val1_a = 'secondary_profile_name'
        val1_b = 'secondary_network_name'
        for x in _mapping:
            if (x[val1_a] is None or x[val1_b] is None):
                print("%s[ERROR] The following network mapping is not "
                      "initialized in var file mapping:\n"
                      "  %s:'%s'\n  %s:'%s'"
                      % (self.prefix, val1_a, x[val1_a], val1_b, x[val1_b]))
                exit()
            map_key = x[val1_a] + "_" + x[val1_b]
            if map_key in _secondary1:
                _return_set.add(map_key)
            else:
                _secondary1.add(map_key)

        # Check for duplicates in primary_profile_id
        _primary2 = set()
        key = 'primary_profile_id'
        _return_set.update(set(x[key]
                               for x in _mapping if
                               x[key] in _primary2 or
                               _primary2.add(x[key])))

        # Check for duplicates in secondary_profile_id
        _secondary2 = set()
        val = 'secondary_profile_id'
        _return_set.update(set(x[val]
                               for x in _mapping if
                               x[val] in _secondary2 or
                               _secondary2.add(x[val])))
        return _return_set


class DefaultOption(dict):

    def __init__(self, config, section, **kv):
        self._config = config
        self._section = section
        dict.__init__(self, **kv)

    def items(self):
        _items = []
        for option in self:
            if not self._config.has_option(self._section, option):
                _items.append((option, self[option]))
            else:
                value_in_config = self._config.get(self._section, option)
                _items.append((option, value_in_config))
        return _items


class ConnectSDK:
    primary_url, primary_user, primary_ca, primary_password = '', '', '', ''
    secondary_url, secondary_user, secondary_ca, secondary_password = '', '', '', ''
    prefix = ''
    error_msg = "%s[ERROR] The '%s' field in the %s setup is not " \
                "initialized in var file mapping."

    def __init__(self, var_file, prefix):
        """
        ---
        dr_sites_primary_url: http://xxx.xx.xx.xxx:8080/ovirt-engine/api
        dr_sites_primary_username: admin@internal
        dr_sites_primary_ca_file: /etc/pki/ovirt-engine/ca.pem

        # Please fill in the following properties for the secondary site:
        dr_sites_secondary_url: http://yyy.yy.yy.yyy:8080/ovirt-engine/api
        dr_sites_secondary_username: admin@internal
        dr_sites_secondary_ca_file: /etc/pki/ovirt-engine_secondary/ca.pem
        """
        self.primary_url = var_file.get('dr_sites_primary_url')
        self.primary_user = var_file.get('dr_sites_primary_username')
        self.primary_ca = var_file.get('dr_sites_primary_ca_file')
        # TODO
        self.primary_password = "12"
        self.secondary_url = var_file.get('dr_sites_secondary_url')
        self.secondary_user = var_file.get('dr_sites_secondary_username')
        self.secondary_ca = var_file.get('dr_sites_secondary_ca_file')
        # TODO
        self.secondary_password = "12"
        self.prefix = prefix

    def validate_primary(self):
        isValid = True
        if self.primary_url is None:
            print(self.error_msg % (self.prefix, "url", "primary"))
            isValid = False
        if self.primary_user is None:
            print(self.error_msg % (self.prefix, "username", "primary"))
            isValid = False
        if self.primary_password is None:
            print(self.error_msg % (self.prefix, "password", "primary"))
            isValid = False
        if self.primary_ca is None:
            print(self.error_msg % (self.prefix, "ca", "primary"))
            isValid = False
        return isValid

    def validate_secondary(self):
        isValid = True
        if self.secondary_url is None:
            print(self.error_msg % (self.prefix, "url", "secondary"))
            isValid = False
        if self.secondary_user is None:
            print(self.error_msg % (self.prefix, "username", "secondary"))
            isValid = False
        if self.secondary_password is None:
            print(self.error_msg % (self.prefix, "password", "secondary"))
            isValid = False
        if self.secondary_ca is None:
            print(self.error_msg % (self.prefix, "ca", "secondary"))
            isValid = False
        return isValid

    def connect_primary(self):
        return self._connect_sdk(self.primary_url,
                                 self.primary_user,
                                 self.primary_password,
                                 self.primary_ca)

    def connect_secondary(self):
        return self._connect_sdk(self.secondary_url,
                                 self.secondary_user,
                                 self.secondary_password,
                                 self.secondary_ca)

    def _connect_sdk(self, url, username, password, ca):
        connection = sdk.Connection(
            url=url,
            username=username,
            password=password,
            ca_file=ca,
        )
        return connection


if __name__ == "__main__":
    ValidateMappingFile().run()
