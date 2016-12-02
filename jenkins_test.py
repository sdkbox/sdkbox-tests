#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
 _______ ______  _     _ ______   _____  _     _
 |______ |     \ |____/  |_____] |     |  \___/
 ______| |_____/ |    \_ |_____] |_____| _/   \_
Copyright (c) 2015-2016 SDKBox Inc.
"""

# 0. download sdkbox_installer.zip
# 1. install lots of plugins into [lua,cpp,js]/[226,300,...]
# 2. compile [ios,android,android-studio]


import getopt
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import traceback
import types
import urllib2
import zipfile
import random

ALL_CASES = [

    [
        'appodeal',
    ],

    [
        'agecheq',
        'adcolony',
        'chartboost',
        'flurryanalytics',
        'googleanalytics',
        'iap',
        'playphone',
        'review',
        'admob',
        'share'
    ],
    [
        'appnext',
        'iap',
        'playphone',
        'amazon',
        'admob',
        'sdkboxads',
        'fyber',
        'tune',
        'leadbolt',
        'apteligent',
        'kochava',
    ],
    [
        'valuepotion',
        'youtube', # target = 21
        'onesignal',
        'inmobi',
    ],
    [
        'facebook',
        'tune',
        'share',
    ]

    # [
    #     'bee7'  # target = 21
    # ]

    # [
    #     'scientificrevenue'  # using different core
    # ],

    # AnySDK ?
    # [
    #     'anysdk'
    # ]
]


class Utils:
    """ platforms """
    PLATFORM_MAC = 1
    PLATFORM_WINDOWS = 2
    PLATFORM_LINUX = 3

    def __init__(self):
        pass

    @staticmethod
    def curl(url, destination=None, chunk_size=None, callback=None):
        try:
            response = urllib2.urlopen(url)
            if chunk_size is None:
                data = response.read()
            else:
                data = ''
                size = 0
                total_size = response.headers['content-length']
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    size += len(chunk)
                    if callback is not None:
                        callback(size, total_size)
                    data += chunk
        except Exception as e:
            print(e)
            print('ERROR! url:' + url)
            return None
        if destination is not None:
            Utils.create_dir_if(destination)
            f = open(destination, 'wb')
            if not f:
                print('ERROR! can not open file:' + destination)
                return None
            f.write(data)
            f.close()
        if callback is not None:  # the cursor flyback needs a blank line after
            print ''
        return data

    @staticmethod
    def progress_bar(amount, total, width=35):
        perc = 100 * int(amount) / int(total)
        on = width * perc / 100
        off = width - on
        s = '[' + on * '#' + off * ' ' + '] ' + str(perc) + '%'
        if Utils.platform() == Utils.PLATFORM_WINDOWS:
            print s + '\r',
        else:
            print s + '\033[1A'

    @staticmethod
    def create_dir_if(path):
        if os.path.exists(path):
            return
        if path.endswith('/'):
            os.makedirs(path)
            return
        else:
            dir_name = os.path.dirname(path)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)

    @staticmethod
    def calculate_sha1(data):
        hasher = hashlib.sha1()
        hasher.update(data)
        sha1 = hasher.hexdigest()
        return sha1

    @staticmethod
    def platform():
        p = platform.system()
        if p == 'Windows':
            return Utils.PLATFORM_WINDOWS
        elif p.startswith('Linux'):
            return Utils.PLATFORM_LINUX
        elif p == 'Darwin':
            return Utils.PLATFORM_MAC
        raise RuntimeError('unsupported platform ' + p)

    @staticmethod
    def unzip_file(path, out_dir=None):
        if path.endswith('.zip'):
            f = open(path, 'rb')
            dir_name = out_dir
            if dir_name is None:
                dir_name = os.path.dirname(path)
            z = zipfile.ZipFile(f)
            for info in z.infolist():
                n = info.filename
                outfile = open(os.path.join(dir_name, n), 'wb')
                try:
                    data = z.read(n)
                except:
                    raise RuntimeError('failed to find ' + n + 'in archive ' + path)
                outfile.write(data)
                outfile.close()
                unix_attributes = info.external_attr >> 16
                if unix_attributes:
                    os.chmod(os.path.join(dir_name, n), unix_attributes)
            f.close()

    @staticmethod
    def has_cmd(name):
        from distutils import spawn
        cmd_path = spawn.find_executable(name)

        if cmd_path is not None:
            return True
        else:
            return False


def download_installer(path, info):
    response = Utils.curl(info['url'], None, 1024, Utils.progress_bar)
    sha1 = Utils.calculate_sha1(response)
    if sha1 != info['sha1']:
        raise RuntimeError('ERROR! SHA1 of update does not match\nFound  : ' + sha1 + '\nNeeded : ' + info['sha1'])

    try:
        Utils.create_dir_if(path)
        f = open(path, 'wb')
        f.write(response)
        f.close()
    except:
        raise RuntimeError('ERROR! failed to save updated SDKBOX')

    return path


def get_installer_url(is_staging):
    if is_staging:
        url = 'http://staging.sdkbox.com/installer/v1/'
    else:
        url = 'http://download.sdkbox.com/installer/v1/'

    manifest_url = os.path.join(url, 'manifest.json')
    print '# Get manifest url: ' + manifest_url
    req = urllib2.Request(manifest_url)
    response = urllib2.urlopen(req)
    data = response.read()
    if not data or 0 == len(data):
        raise Exception('ERROR! load manifest fail')
    manifest = json.loads(data)

    key = 'packages'
    if key not in manifest:
        raise Exception('ERROR! manifest format error')
    manifest = manifest[key]

    key = 'SDKBOX'
    if key not in manifest:
        raise Exception('ERROR! manifest format error')
    manifest = manifest[key]

    key = 'versions'
    if key not in manifest:
        raise Exception('ERROR! manifest format error')
    manifest = manifest[key]

    keys = manifest.keys()
    keys.sort()
    l = keys[-1:]
    if len(l):
        l = l[0]
    manifest = manifest[l]

    if 'bundle' not in manifest or 'sha1' not in manifest:
        raise Exception('ERROR! manifest format error')

    return {'url': url + manifest['bundle'] + '?' + str(random.randint(0, 10000000)), 'bundle': manifest['bundle'], 'sha1': manifest['sha1']}


def print_usage():
    print '''Usage: {file}
                    -p <TemplateProjectFolder>
                    -g <plugin1,plugin2. test all plugins as default>
                    [-l <lang and version, ex. cpp300, lua226, etc.>]
                    [--platform <ios | android>]
                    [--china, use china server for installer]
                    [--staging, use test server for installer]
                    [--use_cached_package, don't download plugin package each time]

    # Test all plugins with staging server
    {file} -p /var/cocos/cpp226/projects/cpp226 --staging

    # Test one plugin with staging server
    {file} -p /var/cocos/cpp226/projects/cpp226 -g adcolony --staging

    # Test one more plugins with staging server
    {file} -p /var/cocos/cpp226/projects/cpp226 -g adcolony,playphone --staging

    # Test more and more cases
    {file} -p /var/cocos/cpp300 -g adcolony,playphone:facebook --staging

    '''.format(file=os.path.basename(__file__))

    sys.exit(2)


def get_curr_path():
    return os.path.dirname(os.path.realpath(__file__))


def get_sdkbox_dir():
    sdkbox_installer_dir = os.path.join(get_curr_path(), '.sdkbox', 'bin')
    print 'sdkbox installer dir: ' + sdkbox_installer_dir
    return sdkbox_installer_dir


def get_sdkbox_path():
    sdkbox_exec_file = 'sdkbox.bat' if Utils.platform() == Utils.PLATFORM_WINDOWS else 'sdkbox'
    sdkbox_installer_path = os.path.join(get_sdkbox_dir(), sdkbox_exec_file)
    print 'sdkbox installer path: ' + sdkbox_installer_path
    return sdkbox_installer_path


def trim_folder(f):
    return os.path.abspath(f).rstrip('/')


def update_android_226_project(project_path):
    def get_api_level(target_str, raise_error=True):
        special_targets_info = {
            'android-4.2': 17,
            'android-L': 20
        }

        if special_targets_info.has_key(target_str):
            ret = special_targets_info[target_str]
        else:
            match = re.match(r'android-(\d+)', target_str)
            if match is not None:
                ret = int(match.group(1))
            else:
                if raise_error:
                    raise Exception('COMPILE_ERROR_NOT_VALID_AP_FMT', target_str)
                else:
                    ret = -1

        return ret

    def get_target_config(proj_path):
        property_file = os.path.join(proj_path, 'project.properties')
        if not os.path.isfile(property_file):
            raise Exception('COMPILE_ERROR_FILE_NOT_FOUND_FMT', property_file)

        patten = re.compile(r'^target=(.+)')
        for line in open(property_file):
            str1 = line.replace(' ', '')
            str2 = str1.replace('\t', '')
            match = patten.match(str2)
            if match is not None:
                target = match.group(1)
                target_num = get_api_level(target)
                if target_num > 0:
                    return target_num

        raise Exception('COMPILE_ERROR_TARGET_NOT_FOUND_FMT', property_file)

    def select_default_android_platform(min_api_level):
        """ select a default android platform in SDK_ROOT
        """

        sdk_root = os.environ['ANDROID_SDK_ROOT']
        platforms_dir = os.path.join(sdk_root, 'platforms')
        ret_num = -1
        ret_platform = ''
        if os.path.isdir(platforms_dir):
            for dir_name in os.listdir(platforms_dir):
                if not os.path.isdir(os.path.join(platforms_dir, dir_name)):
                    continue

                num = get_api_level(dir_name, raise_error=False)
                if num >= min_api_level:
                    if ret_num == -1 or ret_num > num:
                        ret_num = num
                        ret_platform = dir_name

        if ret_num != -1:
            return ret_platform
        else:
            return None

    def check_android_platform(android_platform, proj_path, auto_select):
        sdk_root = os.environ['ANDROID_SDK_ROOT']
        ret = android_platform
        min_platform = get_target_config(proj_path)
        if android_platform is None:
            # not specified platform, found one
            ret = select_default_android_platform(min_platform)
        else:
            # check whether it's larger than min_platform
            select_api_level = get_api_level(android_platform)
            if select_api_level < min_platform:
                if auto_select:
                    # select one for project
                    ret = select_default_android_platform(min_platform)
                else:
                    # raise error
                    raise Exception('COMPILE_ERROR_AP_TOO_LOW_FMT', proj_path)

        if ret is None:
            raise Exception('COMPILE_ERROR_AP_NOT_FOUND_FMT', proj_path)

        ret_path = os.path.join(sdk_root, 'platforms', ret)
        if not os.path.isdir(ret_path):
            raise Exception('COMPILE_ERROR_NO_AP_IN_SDK_FMT', ret)

        special_platforms_info = {
            'android-4.2': 'android-17'
        }
        if special_platforms_info.has_key(ret):
            ret = special_platforms_info[ret]

        return ret

    def update_lib_projects(sdk_tool_path, android_platform, property_path):
        sdk_root = os.environ['ANDROID_SDK_ROOT']

        property_file = os.path.join(property_path, 'project.properties')
        if not os.path.isfile(property_file):
            return

        patten = re.compile(r'^android\.library\.reference\.[\d]+=(.+)')
        for line in open(property_file):
            str1 = line.replace(' ', '')
            str2 = str1.replace('\t', '')
            match = patten.match(str2)
            if match is not None:
                # a lib project is found
                lib_path = match.group(1)
                abs_lib_path = os.path.join(property_path, lib_path)
                abs_lib_path = os.path.normpath(abs_lib_path)
                if os.path.isdir(abs_lib_path):
                    target_str = check_android_platform(android_platform, abs_lib_path, True)
                    cmd = [sdk_tool_path, 'update', 'lib-project', '-t', target_str, '-p', abs_lib_path]
                    print '# ' + ' '.join(cmd)
                    subprocess.check_call(cmd)

                    update_lib_projects(sdk_tool_path, android_platform, abs_lib_path)

    sdk_root = os.environ['ANDROID_SDK_ROOT']
    sdk_tool_path = os.path.join(sdk_root, 'tools', 'android')
    android_platform = None

    # check the android platform
    print '# check the android platform'
    target_str = check_android_platform(android_platform, project_path, False)
    print '# the android platform is ' + target_str

    # update project
    print '# update android project'
    cmd = [sdk_tool_path, 'update', 'project', '-t', target_str, '-p', project_path]
    print '# ' + ' '.join(cmd)
    subprocess.check_call(cmd)

    # update lib-projects
    print '# update android lib-projects'
    update_lib_projects(sdk_tool_path, android_platform, project_path)


def supports_android_studio(proj):
    p = os.path.join(proj, '../proj.android-studio')
    print '# There is android-studio ' + str(os.path.exists(p))
    return os.path.exists(p)


def build_android(proj, cocos_version):
    print '# build project for android platform.'
    try:
        if cocos_version == 'v2':
            cur_dir = os.getcwd()
            os.chdir(proj)
            print(proj + '/build_native.sh')
            update_android_226_project(proj)
            subprocess.check_call(proj + '/build_native.sh', shell=True, cwd=proj)
            subprocess.check_call('ant debug', shell=True, cwd=proj)
            os.chdir(cur_dir)
        else:
            subprocess.check_call(['cocos', 'compile', '-s', proj, '-p', 'android', '-j', '8'])
            if supports_android_studio(proj):
                subprocess.check_call(
                        ['cocos', 'compile', '-s', proj, '-p', 'android', '-j', '8', '--android-studio'])
    except subprocess.CalledProcessError as e:
        if type(e.cmd) is types.StringType:
            print '# build android FAILED. execute command error: ' + e.cmd
        else:
            print '# build android FAILED. execute command error: ' + ' '.join(e.cmd)
        return e.returncode
    except Exception as e:
        print '# build android FAILED. error:' + str(e)
        return 1

    print '# build project for android platform SUCCESS.'
    return 0


def build_ios(proj, cocos_version):
    print '# build project for ios platform.'
    try:
        if cocos_version == 'v2':
            cur_dir = os.getcwd()
            os.chdir(proj)

            # get sdk
            output = subprocess.check_output(['xcodebuild', '-showsdks'])
            result = re.search('iphonesimulator.+', output)
            sdk = result.group(0)

            cmd = ['xcodebuild', 'ONLY_ACTIVE_ARCH=YES', '-sdk', sdk, 'VALID_ARCHS=i386', '-configuration', 'Release']

            subprocess.check_call(cmd)
            os.chdir(cur_dir)
        else:
            cmd = ['cocos', 'compile', '-s', proj, '-p', 'ios', '-j', '8']

            subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print '# build ios FAILED. command: ' + ' '.join(e.cmd)
        return e.returncode
    except Exception as e:
        print '# build ios FAILED. error:' + str(e)
        return 1

    print '# build project for ios platform  SUCCESS.'
    return 0


def find_ios_proj(root, cocos_version):
    print '# find project within: ' + root

    if not os.path.isdir(root):
        return ''

    if cocos_version == 'v2':
        if os.path.isdir(root + '/proj.ios'):
            return root + '/proj.ios'  # cpp v2
        else:
            print '# template dir is not a project dir'
    else:
        if os.path.isdir(root + '/frameworks/runtime-src/proj.ios_mac'):  # js & lua v3
            return root + '/frameworks/runtime-src/proj.ios_mac'
        elif os.path.isdir(root + '/proj.ios_mac'):
            return root + '/proj.ios_mac'  # cpp v3
        else:
            print '# template dir is not a project dir'

    return ''


def clean_up(template_dir, cocos_version):
    if cocos_version == 'v2':
        clean_dir = os.path.join(template_dir, '../..')
    else:
        clean_dir = template_dir

    subprocess.Popen(['git', 'clean', '-dxf'], cwd=clean_dir).wait()
    subprocess.Popen(['git', 'checkout', '-f'], cwd=clean_dir).wait()

    return 0


def get_test_case(argv):
    ret = []
    if argv == '':
        ret = ALL_CASES
    elif ':' in argv:
        args = argv.split(':')
        for arg in args:
            ret.append(arg.split(','))
    elif ',' in argv:
        ret.append(argv.split(','))
    else:
        ret.append([argv])
    return ret


def clean_sdkbox_cache():
    from os.path import expanduser
    home_dir = expanduser("~")
    sdkbox_home = os.path.join(home_dir, '.sdkbox')
    sdkbox_plugin_dir = os.path.join(sdkbox_home, 'plugins')
    sdkbox_log_dir = os.path.join(sdkbox_home, 'log')
    sdkbox_cache_dir = os.path.join(sdkbox_home, 'cache')

    if os.path.isdir(sdkbox_plugin_dir):
        print 'Removing ' + sdkbox_plugin_dir
        shutil.rmtree(sdkbox_plugin_dir)

    if os.path.isdir(sdkbox_log_dir):
        print 'Removing ' + sdkbox_log_dir
        shutil.rmtree(sdkbox_log_dir)

    if os.path.isdir(sdkbox_cache_dir):
        print 'Removing ' + sdkbox_cache_dir
        shutil.rmtree(sdkbox_cache_dir)


def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'p:g:l:', ['china', 'staging', 'platform=', 'use_cached_package'])
    except getopt.GetoptError:
        print_usage()

    template_dir = ''
    lang_ver = ''
    cocos_version = ''
    installer_server = ''
    platform = ''
    cases = ALL_CASES
    use_cached_package = False

    for opt, arg in opts:
        if opt == '-p':
            template_dir = trim_folder(arg)
        if opt == '-g':
            cases = get_test_case(arg)
        if opt == '-l':
            lang_ver = arg
        if opt == '--china':
            installer_server = '--china'
        if opt == '--staging':
            installer_server = '--staging'
        if opt == '--platform':
            platform = arg
        if opt == '--use_cached_package':
            use_cached_package = True

    if template_dir == '':
        print_usage()

    print '# Clean sdkbox cache'
    clean_sdkbox_cache()

    print '# Check sdkbox installer directory'
    SDKBOX_INSTALLER_DIR = os.path.join(get_curr_path(), '.sdkbox')
    if os.path.exists(SDKBOX_INSTALLER_DIR):
        shutil.rmtree(SDKBOX_INSTALLER_DIR)

    print '# Download sdkbox installer'
    info = get_installer_url(installer_server == '--staging')
    path = os.path.join(SDKBOX_INSTALLER_DIR, 'bin', info['bundle'])
    download_installer(path, info)
    Utils.unzip_file(path)

    if lang_ver == '':
        print '# As lang and version are not specified, get them from template dir name.'
        lang_ver = os.path.split(template_dir)[1]

    # Detect cocos version
    reg = re.compile('\D+(\d+)')
    cocos_ver_num = reg.match(lang_ver).group(1)
    if cocos_ver_num.startswith('3'):
        cocos_version = 'v3'
    else:
        cocos_version = 'v2'

    if not os.path.isdir(template_dir):
        print '# template not found: ' + template_dir
        return 7

    print '# Remove sdkbox cache.'
    cache_dir = os.path.expanduser('~/.sdkbox/cache')
    if os.path.exists(cache_dir): shutil.rmtree(cache_dir)

    ios_proj = find_ios_proj(template_dir, cocos_version)
    if ios_proj == '':
        return 1
    android_proj = os.path.abspath(ios_proj + '/../proj.android')
    sdkbox_path = get_sdkbox_path()

    for plugins in cases:
        print '# Clean up.'
        clean_up(template_dir, cocos_version)

        for plugin_name in plugins:
            print '# Install plugin ' + plugin_name
            cmd = [sdkbox_path, 'import', plugin_name, '-p', template_dir, '--nohelp', '--noupdate']
            if not use_cached_package:
                cmd.append('--forcedownload')
            if installer_server != '':
                cmd.append(installer_server)
            print '# Call: ' + ' '.join(cmd)

            # time out, try 10 times
            exitno = 0
            for x in xrange(1,10):
                exitno = subprocess.call(cmd)
                if exitno != 10:   # timeout code
                    break

            if exitno != 0:
                return 1

        if platform != 'android':
            if build_ios(ios_proj, cocos_version) != 0:
                return 1
        if platform != 'ios':
            if build_android(android_proj, cocos_version) != 0:
                return 1

    print '# All Done.'

    print '# Clean up.'
    clean_up(template_dir, cocos_version)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
