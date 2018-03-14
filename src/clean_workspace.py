import json
import os
import sys
from argparse import ArgumentParser
from datetime import datetime

import P4

ACTIVE_PROJECTS = ['int8', 'int9']
CLEANUP_REGISTER_PATH = os.path.join(os.getenv('TEMP', 'Z:\\temp'), 'data-workspace-clean.txt')
DATA_CLIENT_FILE = 'SM_P4DATACLIENT.txt'


def register_record_delete(cleanup_meta, project, path, dry_run=False):
    if dry_run:
        print "\t Dry-run activated: record would be delete '{}'".format(cleanup_meta['projects'][project][path])
    else:
        print "\t Missing file {}. Deleting record".format(path)
        del cleanup_meta['projects'][project][path]

    register_save(cleanup_meta)


def sorted_list(cleanup_meta):
    file_list = []

    if 'projects' in cleanup_meta:
        for project in cleanup_meta['projects']:
            for file in cleanup_meta['projects'][project]:
                for i in range(0, len(file_list)):
                    efile = file_list[i]['path']
                    project_files = cleanup_meta['projects'][project]

                    if project_files[file]['modified'] < project_files[efile]['modified']:
                        file_list.insert(i, {'project': project, 'path': file})
                        break

                if {'project': project, 'path': file} not in file_list:
                    file_list.append({'project': project, 'path': file})

    return file_list


def clean_directories(p4, cleanup_meta, limit, dry_run):
    print('Cleaning limited to {} directories'.format(limit))
    count = 0

    for item in sorted_list(cleanup_meta):
        count += 1

        if count > int(limit):
            break

        if os.path.exists(item['path']):
            register_record_update(cleanup_meta, item['project'], item['path'], 'pending', dry_run)
            p4_clean(p4, item['project'], item['path'], dry_run)
            register_record_update(cleanup_meta, item['project'], item['path'], 'success', dry_run)
        else:
            register_record_delete(cleanup_meta, item['project'], item['path'], dry_run)
            count -= 1


def register_record_update(cleanup_meta, project, path, state, dry_run=False):
    if state == 'unset':
        time_now = 0
    else:
        time_now = datetime.now().strftime("%Y%m%d-%H%M%S")

    path_record = {'status': state, 'project': project, 'modified': time_now}

    if dry_run:
        print "\t Dry-run activated: record would be set to '{}'".format(path_record)
    else:
        cleanup_meta['projects'][project][path] = path_record

    register_save(cleanup_meta)


def register_record_initialize(cleanup_meta, project, dry_run):
    project_path = get_project_path(project)

    project_directories = [f for f in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, f))]

    for directory in project_directories:
        path = os.path.join(project_path, directory)
        if path not in cleanup_meta['projects'][project]:
            print 'intializing {}'.format(path)
            register_record_update(cleanup_meta, project, path, 'unset', dry_run)


def p4_client(project):
    HOSTNAME = os.getenv('HOSTNAME', os.getenv('COMPUTERNAME').lower())

    p4client = '{}-{}-data'.format(HOSTNAME, project)
    project_path = get_project_path(project)
    dataclientfile = os.path.join(project_path, DATA_CLIENT_FILE)

    if os.path.isfile(dataclientfile):
        with open(dataclientfile, 'rt') as f:
            p4client = f.read().strip()

    return p4client


def p4_clean(p4, project, clean_path, dry_run=False):
    if os.path.isfile(clean_path):
        p4_run_args = ['clean', clean_path]
    else:
        p4_run_args = ['clean', '{}\...'.format(clean_path)]

    try:
        if dry_run:
            print("\t Dry-run activated: 'p4 {}'".format(' '.join(p4_run_args)))
        else:
            print("\t Running 'p4 {}'".format(' '.join(p4_run_args)))
            sys.stdout.flush()

            p4.client = p4_client(project)
            return
            runinfo = p4.run(p4_run_args)
            for runline in runinfo:
                print(runline)
    except P4.P4Exception as e:
        print("P4 error detected in data workspace clean up {}".format(e))


def clean_files(p4, cleanup_meta, project, dry_run):
    project_path = get_project_path(project)

    project_files = [f for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f))]

    for file in project_files:
        p4_clean(p4, project, os.path.join(project_path, file), dry_run)


def get_project_path(project):
    return os.path.join('Z:', os.sep, project)


def register_save(cleanup_meta):
    with open(CLEANUP_REGISTER_PATH, 'w') as cleanup_register:
        cleanup_register.writelines(json.dumps(cleanup_meta, indent=4))


def register_initialize():
    json_register = {'projects': {}}
    register_save(json_register)

    return json_register


def register_meta():
    if not os.path.isfile(CLEANUP_REGISTER_PATH):
        register_initialize()

    register_meta = json.load(open(CLEANUP_REGISTER_PATH, 'r'))

    for project in ACTIVE_PROJECTS:
        if project not in register_meta['projects']:
            register_meta['projects'][project] = {}
            register_save(register_meta)

    return register_meta


def p4_connect():
    p4 = P4.P4()
    p4.prog = "JenkinsCleanup-CleanUpDataWorkspaceSpec"
    p4.exception_level = 1  # do not throw an exception on warnings
    return p4.connect()


def parse_arguments(args=None):
    parser = ArgumentParser()
    parser.add_argument('--limit', type=int, default=2, help='Number of directories to clean within a project')
    parser.add_argument('--dry-run', action='store_true', help='make not changes')
    return parser.parse_args(args)


def main():
    print("Cleaning data workspace")
    args = parse_arguments()
    p4 = p4_connect()

    cleanup_meta = register_meta()

    for project in cleanup_meta['projects']:
        if os.path.exists(get_project_path(project)):
            clean_files(p4, cleanup_meta, project, args.dry_run)
            register_record_initialize(cleanup_meta, project, args.dry_run)

    clean_directories(p4, cleanup_meta, args.limit, args.dry_run)


if __name__ == '__main__':
    main()
