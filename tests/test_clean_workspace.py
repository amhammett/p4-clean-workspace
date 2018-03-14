import os
import unittest

from src import clean_workspace


class TestCleanWorkspace(unittest.TestCase):
    def test_get_project_path(self):
        test_data = [
            {
                "comment": "empty project",
                "input": "",
                "result": "Z:\\"
            }, {
                "comment": "expected project",
                "input": "int",
                "result": "Z:\\int"
            }
        ]

        print("")
        for test_data_record in test_data:
            print("\t Running: {}".format(test_data_record['comment']))
            self.assertEqual(
                clean_workspace.get_project_path(test_data_record['input']),
                test_data_record['result']
            )

    def test_import(self):
        print("")
        self.assertTrue(clean_workspace)

    def test_p4_client(self):
        test_data = [
            {
                "comment": "expcted project",
                "input": "foo",
                "result": "{}-foo-data".format(os.environ['HOSTNAME'])
            }, {
                "comment": "expcted project",
                "input": "bar",
                "env": [
                    {
                        "key": "HOSTNAME",
                        "value": "foo"
                    }
                ],
                "result": "foo-bar-data"
            }, {
                "comment": "empty data",
                "input": "",
                "result": "{}--data".format(os.environ['HOSTNAME'])
            }
        ]

        print("")
        for test_data_record in test_data:
            print("\t Running: {}".format(test_data_record['comment']))
            _os_environ = os.environ.copy()

            if 'env' in test_data_record:
                for env_var in test_data_record['env']:
                    os.environ[env_var['key']] = env_var['value']

            self.assertEqual(clean_workspace.p4_client(test_data_record['input']), test_data_record['result'])
            os.environ.clear()
            os.environ.update(_os_environ)

    def test_p4_connect(self):
        print("")
        self.assertTrue(clean_workspace.p4_connect())

    def test_parse_argument(self):
        test_data = [
            {
                "comment": "empty data",
                "input": [],
                "result": {
                    "args": [
                        {
                            "key": "dry_run",
                            "value": False
                        }
                    ]
                }
            }, {
                "comment": "enable dry run",
                "input": ['--dry-run'],
                "result": {
                    "args": [
                        {
                            "key": "dry_run",
                            "value": True
                        }
                    ]
                }
            }, {
                "comment": "verify limit",
                "input": ['--limit=5'],
                "result": {
                    "args": [
                        {
                            "key": "limit",
                            "value": 5
                        }
                    ]
                }
            }
        ]

        print("")
        for test_data_record in test_data:
            print("\t Running: {}".format(test_data_record['comment']))
            args = clean_workspace.parse_arguments(test_data_record['input'])
            args_dict = vars(args)

            for result_args in test_data_record['result']['args']:
                self.assertEqual(result_args['value'], args_dict[result_args['key']])

    def test_sorted_list_empty(self):
        test_data = [
            {
                "comment": "project without files",
                "input": {"projects": {"foo": {}}},
                "result": []
            }, {
                "comment": "empty projects",
                "input": {"projects": {}},
                "result": []
            }, {
                "comment": "empty object",
                "input": {},
                "result": []
            }, {
                "comment": "garbage object",
                "input": {"foo": "bar"},
                "result": []
            }, {
                "comment": "empty array",
                "input": [],
                "result": []
            }, {
                "comment": "numbered array",
                "input": [1, 2, 3],
                "result": []
            }
        ]

        print("")
        for test_data_record in test_data:
            print("\t Running: {}".format(test_data_record['comment']))
            self.assertEqual(clean_workspace.sorted_list(test_data_record['input']), test_data_record['result'])

    def test_sorted_list_with_projects(self):
        test_data = [
            {
                "comment": "project with single file",
                "input": {
                    "projects": {
                        "foo": {
                            "./tests/foo": {
                                "status": "success",
                                "project": "foo",
                                "modified": "2017"
                            }
                        }
                    }
                },
                "result": [
                    {
                        "path": "./tests/foo",
                        "project": "foo"
                    }
                ]
            }, {
                "comment": "project with multiple files",
                "input": {
                    "projects": {
                        "foo": {
                            "./tests/foo": {
                                "status": "success",
                                "project": "foo",
                                "modified": "2017"
                            },
                            "./tests/bar": {
                                "status": "success",
                                "project": "foo",
                                "modified": "2018"
                            }
                        }
                    }
                },
                "result": [
                    {
                        "path": "./tests/foo",
                        "project": "foo"
                    },
                    {
                        "path": "./tests/bar",
                        "project": "foo"
                    }
                ]
            }
        ]

        print("")
        for test_data_record in test_data:
            print("\t Running: {}".format(test_data_record['comment']))
            self.assertEqual(clean_workspace.sorted_list(test_data_record['input']), test_data_record['result'])
