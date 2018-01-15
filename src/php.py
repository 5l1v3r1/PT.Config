from configparser import *
from baseconfig import Config, MatchingNode


class Php(Config):
    conftype = 'php.ini'

    def __init__(self, path, options):
        Config.__init__(self, path, options)
        self.config = PhpConf().parse(path).config

    def find_nodes(self, name, context=None):
        if self.has(name):
            return [self.config[name]]

        return []

    def get_node_value(self, node):
        return node.value

    def get_lineno(self, node):
        return node.lineno

    def has(self, option):
        for opt_name in self.config:
            if option in opt_name:
                return True
        return False

    def fill_missing_line(self, option, value, context=None):
        return option + ' = ' + value

    def biggerThan(self, option, advice):
        factor = {'k': 1024,
                  'm': 1024 ** 2,
                  'g': 1024 ** 3
                  }
        option_int = int(option) if option.isdigit() else int(option[:-1]) * factor[option[-1:].lower()]
        advice_int = int(advice) if advice.isdigit() else int(advice[:-1]) * factor[advice[-1:].lower()]

        return True if option_int > advice_int else False


class PhpConf(RawConfigParser):
    config = {}

    def parse(self, path):

        config = {}
        self._read(open(path), path)

        for section in self.sections():
            for (key, value) in self.items(section):
                if key not in allowedDirectives:
                    continue
                valueLowerCase = value['optval'].lower()

                if valueLowerCase in ['on', 'true', '1', ]:
                    value['optval'] = '1'
                elif valueLowerCase in ['false', 'off', 'no', '0']:
                    value['optval'] = '0'
                elif value['optval'] in ['null', 'none', '']:
                    value['optval'] = ''

                config[key] = MatchingNode(key, value['optval'], value['lineno'])

        self.config = config

        return self

    def _read(self, fp, fpname):  # redefinition of a standard method

        cursect = None  # None, or a dictionary
        optname = None
        lineno = 0
        e = None  # None, or an exception
        while True:
            line = fp.readline()
            if not line:
                break
            lineno = lineno + 1
            # comment or blank line?
            if line.strip() == '' or line[0] in '#;':
                continue
            if line.split(None, 1)[0].lower() == 'rem' and line[0] in "rR":
                # no leading whitespace
                continue
                # continuation line?
            if line[0].isspace() and cursect is not None and optname:
                value = line.strip()
                if value:
                    cursect[optname].append(value)
            # a section header or option header?
            else:
                # is it a section header?
                mo = self.SECTCRE.match(line)
                if mo:
                    sectname = mo.group('header')
                    if sectname in self._sections:
                        cursect = self._sections[sectname]
                    elif sectname == DEFAULTSECT:
                        cursect = self._defaults
                    else:
                        cursect = self._dict()
                        cursect['__name__'] = sectname
                        self._sections[sectname] = cursect
                        # So sections can't start with a continuation line
                    optname = None
                # no section header in the file?
                elif cursect is None:
                    raise MissingSectionHeaderError(fpname, lineno, line)
                # an option line?
                else:
                    mo = self._optcre.match(line)
                    if mo:
                        optname, vi, optval = mo.group('option', 'vi', 'value')

                        optname = optname.rstrip()
                        # This check is fine because the OPTCRE cannot
                        # match if it would set optval to None
                        if optval is not None:
                            if vi in ('=', ':') and ';' in optval:
                                # ';' is a comment delimiter only if it follows
                                # a spacing character
                                pos = optval.find(';')
                                if pos != -1 and optval[pos - 1].isspace():
                                    optval = optval[:pos]
                            optval = optval.strip()
                            # allow empty values
                            if optval == '""':
                                optval = ''
                            cursect[optname] = {'optval': optval, 'lineno': lineno}
                        else:
                            # valueless option handling
                            cursect[optname] = optval
                    else:
                        # a non-fatal parsing error occurred.  set up the
                        # exception but keep going. the exception will be
                        # raised at the end of the file and will contain a
                        # list of all bogus lines
                        if not e:
                            e = ParsingError(fpname)
                        e.append(lineno, repr(line))
                        # if any parsing errors occurred, raise an exception
        if e:
            raise e


allowedDirectives = [
    'allow_call_time_pass_reference', 'allow_url_fopen', 'allow_url_include', 'always_populate_raw_post_data',
    'apc.cache_by_default', 'apc.enabled', 'apc.enable_cli', 'apc.file_update_protection', 'apc.filters', 'apc.gc_ttl',
    'apc.include_once_override', 'apc.localcache', 'apc.localcache.size', 'apc.max_file_size', 'apc.mmap_file_mask',
    'apc.num_files_hint', 'apc.optimization', 'apc.report_autofilter', 'apc.rfc1867', 'apc.rfc1867_freq',
    'apc.rfc1867_name', 'apc.rfc1867_prefix', 'apc.shm_segments', 'apc.shm_size', 'apc.slam_defense', 'apc.stat',
    'apc.stat_ctime', 'apc.ttl', 'apc.user_entries_hint', 'apc.user_ttl', 'apc.write_lock', 'apd.bitmask',
    'apd.dumpdir',
    'apd.statement_tracing', 'arg_separator', 'arg_separator.input', 'arg_separator.output', 'asp_tags',
    'assert.active', 'assert.bail', 'assert.callback', 'assert.quiet_eval', 'assert.warning', 'async_send',
    'auto_append_file', 'auto_detect_line_endings', 'auto_globals_jit', 'auto_prepend_file', 'axis2.client_home',
    'axis2.enable_exception', 'axis2.enable_trace', 'axis2.log_path', 'bcmath.scale', 'bcompiler.enabled',
    'blenc.key_file', 'browscap', 'cgi.check_shebang_line', 'cgi.discard_path', 'cgi.fix_pathinfo',
    'cgi.force_redirect',
    'cgi.nph', 'cgi.redirect_status_env', 'cgi.rfc2616_headers', 'child_terminate', 'cli.pager', 'cli.prompt',
    'cli_server.color', 'coin_acceptor.autoreset', 'coin_acceptor.auto_initialize', 'coin_acceptor.auto_reset',
    'coin_acceptor.command_function', 'coin_acceptor.delay', 'coin_acceptor.delay_coins', 'coin_acceptor.delay_prom',
    'coin_acceptor.device', 'coin_acceptor.lock_on_close', 'coin_acceptor.start_unlocked', 'com.allow_dcom',
    'com.autoregister_casesensitive', 'com.autoregister_typelib', 'com.autoregister_verbose', 'com.code_page',
    'com.typelib_file', 'crack.default_dictionary', 'curl.cainfo', 'daffodildb.default_host',
    'daffodildb.default_password', 'daffodildb.default_socket', 'daffodildb.default_user', 'daffodildb.port',
    'date.default_latitude', 'date.default_longitude', 'date.sunrise_zenith', 'date.sunset_zenith', 'date.timezone',
    'dba.default_handler', 'dbx.colnames_case', 'default_charset', 'default_mimetype', 'default_socket_timeout',
    'define_syslog_variables', 'detect_unicode', 'disable_classes', 'disable_functions', 'display_errors',
    'display_startup_errors', 'docref_ext', 'docref_root', 'doc_root', 'enable_dl', 'enable_post_data_reading',
    'engine',
    'error_append_string', 'error_log', 'error_prepend_string', 'error_reporting', 'exif.decode_jis_intel',
    'exif.decode_jis_motorola', 'exif.decode_unicode_intel', 'exif.decode_unicode_motorola', 'exif.encode_jis',
    'exif.encode_unicode', 'exit_on_timeout', 'expect.logfile', 'expect.loguser', 'expect.timeout', 'expose_php',
    'extension', 'extension_dir', 'fastcgi.impersonate', 'fastcgi.logging', 'fbsql.allow_persistant',
    'fbsql.allow_persistent', 'fbsql.autocommit', 'fbsql.batchsize', 'fbsql.batchsize', 'fbsql.default_database',
    'fbsql.default_database_password', 'fbsql.default_host', 'fbsql.default_password', 'fbsql.default_user',
    'fbsql.generate_warnings', 'fbsql.max_connections', 'fbsql.max_links', 'fbsql.max_persistent', 'fbsql.max_results',
    'fbsql.mbatchsize', 'fbsql.show_timestamp_decimals', 'file_uploads', 'filter.default', 'filter.default_flags',
    'from', 'gd.jpeg_ignore_warning', 'geoip.custom_directory', 'geoip.database_standard', 'gpc_order',
    'hidef.ini_path',
    'highlight.bg', 'highlight.comment', 'highlight.default', 'highlight.html', 'highlight.keyword', 'highlight.string',
    'html_errors', 'htscanner.config_file', 'htscanner.default_docroot', 'htscanner.default_ttl',
    'htscanner.stop_on_error', 'http.allowed_methods', 'http.allowed_methods_log', 'http.cache_log',
    'http.composite_log',
    'http.etag.mode', 'http.etag_mode', 'http.force_exit', 'http.log.allowed_methods', 'http.log.cache',
    'http.log.composite', 'http.log.not_found', 'http.log.redirect', 'http.ob_deflate_auto', 'http.ob_deflate_flags',
    'http.ob_inflate_auto', 'http.ob_inflate_flags', 'http.only_exceptions', 'http.persistent.handles.ident',
    'http.persistent.handles.limit', 'http.redirect_log', 'http.request.datashare.connect',
    'http.request.datashare.cookie', 'http.request.datashare.dns', 'http.request.datashare.ssl',
    'http.request.methods.allowed', 'http.request.methods.custom', 'http.send.deflate.start_auto',
    'http.send.deflate.start_flags', 'http.send.inflate.start_auto', 'http.send.inflate.start_flags',
    'http.send.not_found_404', 'hyerwave.allow_persistent', 'hyperwave.allow_persistent', 'hyperwave.default_port',
    'ibase.allow_persistent', 'ibase.dateformat', 'ibase.default_charset', 'ibase.default_db', 'ibase.default_password',
    'ibase.default_user', 'ibase.max_links', 'ibase.max_persistent', 'ibase.timeformat', 'ibase.timestampformat',
    'ibm_db2.binmode', 'ibm_db2.i5_all_pconnect', 'ibm_db2.i5_allow_commit', 'ibm_db2.i5_dbcs_alloc',
    'ibm_db2.instance_name', 'ibm_db2.i5_ignore_userid', 'iconv.input_encoding', 'iconv.internal_encoding',
    'iconv.output_encoding', 'ifx.allow_persistent', 'ifx.blobinfile', 'ifx.byteasvarchar', 'ifx.charasvarchar',
    'ifx.default_host', 'ifx.default_password', 'ifx.default_user', 'ifx.max_links', 'ifx.max_persistent',
    'ifx.nullformat', 'ifx.textasvarchar', 'ignore_repeated_errors', 'ignore_repeated_source', 'ignore_user_abort',
    'imlib2.font_cache_max_size', 'imlib2.font_path', 'implicit_flush', 'include_path', 'intl.default_locale',
    'intl.error_level', 'intl.use_exceptions', 'ingres.allow_persistent', 'ingres.array_index_start', 'ingres.auto',
    'ingres.blob_segment_length', 'ingres.cursor_mode', 'ingres.default_database', 'ingres.default_password',
    'ingres.default_user', 'ingres.describe', 'ingres.fetch_buffer_size', 'ingres.max_links', 'ingres.max_persistent',
    'ingres.reuse_connection', 'ingres.scrollable', 'ingres.trace', 'ingres.trace_connect', 'ingres.utf8',
    'last_modified', 'ldap.base_dn', 'ldap.max_links', 'log.dbm_dir', 'log_errors', 'log_errors_max_len',
    'magic_quotes_gpc', 'magic_quotes_runtime', 'magic_quotes_sybase', 'mail.add_x_header',
    'mail.force_extra_parameters',
    'mail.log', 'mailparse.def_charset', 'maxdb.default_db', 'maxdb.default_host', 'maxdb.default_pw',
    'maxdb.default_user', 'maxdb.long_readlen', 'max_execution_time', 'max_input_nesting_level', 'max_input_vars',
    'max_input_time', 'mbstring.detect_order', 'mbstring.encoding_translation', 'mbstring.func_overload',
    'mbstring.http_input', 'mbstring.http_output', 'mbstring.internal_encoding', 'mbstring.language',
    'mbstring.script_encoding', 'mbstring.http_output_conv_mimetypes', 'mbstring.strict_detection',
    'mbstring.substitute_character', 'mcrypt.algorithms_dir', 'mcrypt.modes_dir', 'memcache.allow_failover',
    'memcache.chunk_size', 'memcache.default_port', 'memcache.hash_function', 'memcache.hash_strategy',
    'memcache.max_failover_attempts', 'memory_limit', 'mime_magic.debug', 'mime_magic.magicfile',
    'mongo.allow_empty_keys', 'mongo.allow_persistent', 'mongo.chunk_size', 'mongo.cmd', 'mongo.default_host',
    'mongo.default_port', 'mongo.is_master_interval', 'mongo.long_as_object', 'mongo.native_long',
    'mongo.ping_interval',
    'mongo.utf8', 'msql.allow_persistent', 'msql.max_links', 'msql.max_persistent', 'mssql.allow_persistent',
    'mssql.batchsize', 'mssql.charset', 'mssql.compatability_mode', 'mssql.connect_timeout', 'mssql.datetimeconvert',
    'mssql.max_links', 'mssql.max_persistent', 'mssql.max_procs', 'mssql.min_error_severity',
    'mssql.min_message_severity', 'mssql.secure_connection', 'mssql.textlimit', 'mssql.textsize', 'mssql.timeout',
    'mysql.allow_local_infile', 'mysql.allow_persistent', 'mysql.max_persistent', 'mysql.max_links', 'mysql.trace_mode',
    'mysql.default_port', 'mysql.default_socket', 'mysql.default_host', 'mysql.default_user', 'mysql.default_password',
    'mysql.connect_timeout', 'mysqli.allow_local_infile', 'mysqli.allow_persistent', 'mysqli.max_persistent',
    'mysqli.max_links', 'mysqli.default_port', 'mysqli.default_socket', 'mysqli.default_host', 'mysqli.default_user',
    'mysqli.default_pw', 'mysqli.reconnect', 'mysqli.cache_size', 'mysqlnd.collect_memory_statistics',
    'mysqlnd.collect_statistics', 'mysqlnd.debug', 'mysqlnd.log_mask', 'mysqlnd.mempool_default_size',
    'mysqlnd.net_cmd_buffer_size', 'mysqlnd.net_read_buffer_size', 'mysqlnd.net_read_timeout',
    'mysqlnd.sha256_server_public_key', 'mysqlnd.trace_alloc', 'mysqlnd_memcache.enable', 'mysqlnd_ms.enable',
    'mysqlnd_ms.force_config_usage', 'mysqlnd_ms.ini_file', 'mysqlnd_ms.config_file', 'mysqlnd_ms.collect_statistics',
    'mysqlnd_ms.multi_master', 'mysqlnd_ms.disable_rw_split', 'mysqlnd_mux.enable', 'mysqlnd_qc.enable_qc',
    'mysqlnd_qc.ttl', 'mysqlnd_qc.cache_by_default', 'mysqlnd_qc.cache_no_table', 'mysqlnd_qc.use_request_time',
    'mysqlnd_qc.time_statistics', 'mysqlnd_qc.collect_statistics', 'mysqlnd_qc.collect_statistics_log_file',
    'mysqlnd_qc.collect_query_trace', 'mysqlnd_qc.query_trace_bt_depth', 'mysqlnd_qc.collect_normalized_query_trace',
    'mysqlnd_qc.ignore_sql_comments', 'mysqlnd_qc.slam_defense', 'mysqlnd_qc.slam_defense_ttl',
    'mysqlnd_qc.std_data_copy', 'mysqlnd_qc.apc_prefix', 'mysqlnd_qc.memc_server', 'mysqlnd_qc.memc_port',
    'mysqlnd_qc.sqlite_data_file', 'mysqlnd_uh.enable', 'mysqlnd_uh.report_wrong_types', 'nsapi.read_timeout',
    'oci8.connection_class', 'oci8.default_prefetch', 'oci8.events', 'oci8.max_persistent',
    'oci8.old_oci_close_semantics', 'oci8.persistent_timeout', 'oci8.ping_interval', 'oci8.privileged_connect',
    'oci8.statement_cache_size', 'odbc.allow_persistent', 'odbc.check_persistent', 'odbc.defaultbinmode',
    'odbc.defaultlrl', 'odbc.default_db', 'odbc.default_cursortype', 'odbc.default_pw', 'odbc.default_user',
    'odbc.max_links', 'odbc.max_persistent', 'odbtp.datetime_format', 'odbtp.detach_default_queries',
    'odbtp.guid_format', 'odbtp.interface_file', 'odbtp.truncation_errors', 'opendirectory.default_separator',
    'opendirectory.max_refs', 'opendirectory.separator', 'open_basedir', 'oracle.allow_persistent', 'oracle.max_links',
    'oracle.max_persistent', 'output_buffering', 'output_handler', 'pam.servicename', 'pcre.backtrack_limit',
    'pcre.recursion_limit', 'pdo.dsn.*', 'pdo_odbc.connection_pooling', 'pdo_odbc.db2_instance_name',
    'pfpro.defaulthost', 'pfpro.defaultport', 'pfpro.defaulttimeout', 'pfpro.proxyaddress', 'pfpro.proxylogon',
    'pfpro.proxypassword', 'pfpro.proxyport', 'pgsql.allow_persistent', 'pgsql.auto_reset_persistent',
    'pgsql.ignore_notice', 'pgsql.log_notice', 'pgsql.max_links', 'pgsql.max_persistent', 'phar.cache_list',
    'phar.extract_list', 'phar.readonly', 'phar.require_hash', 'post_max_size', 'precision', 'printer.default_printer',
    'python.append_path', 'python.prepend_path', 'realpath_cache_size', 'realpath_cache_ttl', 'register_argc_argv',
    'register_globals', 'register_long_arrays', 'report_memleaks', 'report_zend_debug', 'request_order',
    'runkit.internal_override', 'runkit.superglobal', 'safe_mode', 'safe_mode_allowed_env_vars', 'safe_mode_exec_dir',
    'safe_mode_gid', 'safe_mode_include_dir', 'safe_mode_protected_env_vars', 'sendmail_from', 'sendmail_path',
    'serialize_precision', 'session.auto_start', 'session.bug_compat_42', 'session.bug_compat_warn',
    'session.cache_expire', 'session.cache_limiter', 'session.cookie_domain', 'session.cookie_httponly',
    'session.cookie_lifetime', 'session.cookie_path', 'session.cookie_secure', 'session.entropy_file',
    'session.entropy_length', 'session.gc_dividend', 'session.gc_divisor', 'session.gc_maxlifetime',
    'session.gc_probability', 'session.hash_bits_per_character', 'session.hash_function', 'session.name',
    'session.referer_check', 'session.save_handler', 'session.save_path', 'session.serialize_handler',
    'session.upload_progress.cleanup', 'session.upload_progress.enabled', 'session.upload_progress.freq',
    'session.upload_progress.min_freq', 'session.upload_progress.name', 'session.upload_progress.prefix',
    'session.use_strict_mode', 'session.use_cookies', 'session.use_only_cookies', 'session.use_trans_sid',
    'session_pgsql.create_table', 'session_pgsql.db', 'session_pgsql.disable', 'session_pgsql.failover_mode',
    'session_pgsql.gc_interval', 'session_pgsql.keep_expired', 'session_pgsql.sem_file_name',
    'session_pgsql.serializable',
    'session_pgsql.short_circuit', 'session_pgsql.use_app_vars', 'session_pgsql.vacuum_interval', 'short_open_tag',
    'smtp', 'smtp_port', 'soap.wsdl_cache', 'soap.wsdl_cache_dir', 'soap.wsdl_cache_enabled', 'soap.wsdl_cache_limit',
    'soap.wsdl_cache_ttl', 'sql.safe_mode', 'sqlite.assoc_case', 'sqlite3.extension_dir', 'sybase.allow_persistent',
    'sybase.hostname', 'sybase.interface_file', 'sybase.login_timeout', 'sybase.max_links', 'sybase.max_persistent',
    'sybase.min_client_severity', 'sybase.min_error_severity', 'sybase.min_message_severity',
    'sybase.min_server_severity', 'sybase.timeout', 'sybct.allow_persistent', 'sybct.deadlock_retry_count',
    'sybct.hostname', 'sybct.login_timeout', 'sybct.max_links', 'sybct.max_persistent', 'sybct.min_client_severity',
    'sybct.min_server_severity', 'sybct.packet_size', 'sybct.timeout', 'sys_temp_dir', 'sysvshm.init_mem',
    'tidy.clean_output', 'tidy.default_config', 'track_errors', 'track_vars', 'unserialize_callback_func',
    'uploadprogress.file.filename_template', 'upload_max_filesize', 'max_file_uploads', 'upload_tmp_dir',
    'url_rewriter.tags', 'user_agent', 'user_dir', 'user_ini.cache_ttl', 'user_ini.filename', 'valkyrie.auto_validate',
    'valkyrie.config_path', 'variables_order', 'vld.active', 'vld.execute', 'vld.skip_append', 'vld.skip_prepend',
    'windows.show_crt_warning', 'windows_show_crt_warning', 'xbithack', 'xdebug.auto_profile',
    'xdebug.auto_profile_mode',
    'xdebug.auto_trace', 'xdebug.collect_includes', 'xdebug.collect_params', 'xdebug.collect_return',
    'xdebug.collect_vars', 'xdebug.default_enable', 'xdebug.dump.cookie', 'xdebug.dump.env', 'xdebug.dump.files',
    'xdebug.dump.get', 'xdebug.dump.post', 'xdebug.dump.request', 'xdebug.dump.server', 'xdebug.dump.session',
    'xdebug.dump_globals', 'xdebug.dump_once', 'xdebug.dump_undefined', 'xdebug.extended_info', 'xdebug.idekey',
    'xdebug.manual_url', 'xdebug.max_nesting_level', 'xdebug.output_dir', 'xdebug.profiler_aggregate',
    'xdebug.profiler_append', 'xdebug.profiler_enable', 'xdebug.profiler_enable_trigger', 'xdebug.profiler_output_dir',
    'xdebug.profiler_output_name', 'xdebug.remote_autostart', 'xdebug.remote_enable', 'xdebug.remote_handler',
    'xdebug.remote_host', 'xdebug.remote_log', 'xdebug.remote_mode', 'xdebug.remote_port',
    'xdebug.show_exception_trace',
    'xdebug.show_local_vars', 'xdebug.show_mem_delta', 'xdebug.trace_format', 'xdebug.trace_options',
    'xdebug.trace_output_dir', 'xdebug.trace_output_name', 'xdebug.var_display_max_children',
    'xdebug.var_display_max_data', 'xdebug.var_display_max_depth', 'xmlrpc_errors', 'xmlrpc_error_number', 'xmms.path',
    'xmms.session', 'xsl.security_prefs', 'y2k_compliance', 'yami.response.timeout', 'yaz.keepalive', 'yaz.log_file',
    'yaz.log_mask', 'yaz.max_links', 'zend.detect_unicode', 'zend.enable_gc', 'zend.multibyte', 'zend.script_encoding',
    'zend.signal_check', 'zend.ze1_compatibility_mode', 'zend_extension', 'zend_extension_debug',
    'zend_extension_debug_ts', 'zend_extension_ts', 'zlib.output_compression', 'zlib.output_compression_level',
    'zlib.output_handler', 'birdstep.max_links', 'etpan.default.charset', 'etpan.default.protocol', 'ircg.control_user',
    'ircg.keep_alive_interval', 'ircg.max_format_message_sets', 'ircg.shared_mem_size', 'ircg.work_dir',
    'simple_cvs.authmethod', 'simple_cvs.compressionlevel', 'simple_cvs.cvsroot', 'simple_cvs.host',
    'simple_cvs.modulename', 'simple_cvs.username', 'simple_cvs.workingdir', 'velocis.max_links',
]
