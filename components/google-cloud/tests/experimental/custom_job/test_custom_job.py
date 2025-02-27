# Copyright 2021 The Kubeflow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Test Vertex AI Custom Job Client module."""

import unittest
from google_cloud_pipeline_components.experimental.custom_job import custom_job
from kfp import components
from kfp.v2.dsl import component


class VertexAICustomJobUtilsTests(unittest.TestCase):

    def setUp(self):
        super(VertexAICustomJobUtilsTests, self).setUp()
        custom_job._DEFAULT_CUSTOM_JOB_CONTAINER_IMAGE = 'test_launcher_image'

    def _create_a_container_based_component(self) -> callable:
        """Creates a test container based component factory."""

        return components.load_component_from_text("""
name: ContainerComponent
inputs:
- {name: input_text, type: String, description: "Represents an input parameter."}
outputs:
- {name: output_value, type: String, description: "Represents an output paramter."}
implementation:
  container:
    image: google/cloud-sdk:latest
    command:
    - sh
    - -c
    - |
      set -e -x
      echo "$0, this is an output parameter"
    - {inputValue: input_text}
    - {outputPath: output_value}
""")

    def _create_a_pytnon_based_component(self) -> callable:
        """Creates a test python based component factory."""

        @component
        def sum_numbers(a: int, b: int) -> int:
            return a + b

        return sum_numbers

    def test_run_as_vertex_ai_custom_job_on_container_spec_with_defualts_values_converts_correctly(
            self):
        expected_results = {
            'name': 'ContainerComponent',
            'inputs': [{
                'name': 'input_text',
                'type': 'String',
                'description': 'Represents an input parameter.'
            }, {
                'name': 'base_output_directory',
                'type': 'String',
                'optional': True
            }, {
                'name': 'tensorboard',
                'type': 'String',
                'optional': True
            }, {
                'name': 'encryption_spec_key_name',
                'type': 'String',
                'optional': True
            }, {
                'name': 'network',
                'type': 'String',
                'optional': True
            }, {
                'name': 'service_account',
                'type': 'String',
                'optional': True
            }, {
                'name': 'project',
                'type': 'String'
            }, {
                'name': 'location',
                'type': 'String'
            }],
            'outputs': [{
                'name': 'output_value',
                'type': 'String',
                'description': 'Represents an output paramter.'
            }, {
                'name': 'gcp_resources',
                'type': 'String'
            }],
            'implementation': {
                'container': {
                    'image':
                        'test_launcher_image',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--payload',
                        '{"display_name": "ContainerComponent", "job_spec": {"worker_pool_specs": [{"machine_spec": {"machine_type": "n1-standard-4"}, "replica_count": 1, "container_spec": {"image_uri": "google/cloud-sdk:latest", "command": ["sh", "-c", "set -e -x\\necho \\"$0, this is an output parameter\\"\\n", "{{$.inputs.parameters[\'input_text\']}}", "{{$.outputs.parameters[\'output_value\'].output_file}}"]}}], "service_account": "{{$.inputs.parameters[\'service_account}\']}}", "network": "{{$.inputs.parameters[\'network}\']}}", "encryption_spec_key_name": "{{$.inputs.parameters[\'encryption_spec_key_name}\']}}", "tensorboard": "{{$.inputs.parameters[\'tensorboard}\']}}", "base_output_directory": "{{$.inputs.parameters[\'base_output_directory}\']}}"}}',
                        '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        component_factory_function = self._create_a_container_based_component()
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function)
        self.assertDictEqual(custom_job_spec.component_spec.to_dict(),
                             expected_results)

    def test_run_as_vertex_ai_custom_job_on_python_spec_with_defualts_values_converts_correctly(
            self):
        # TODO enable after issue kfp release to support executor input.
        return
        expected_results = {
            'name': 'Sum numbers',
            'inputs': [{
                'name': 'a',
                'type': 'Integer'
            }, {
                'name': 'b',
                'type': 'Integer'
            }, {
                'name': 'project',
                'type': 'String'
            }, {
                'name': 'location',
                'type': 'String'
            }],
            'outputs': [{
                'name': 'Output',
                'type': 'Integer'
            }, {
                'name': 'gcp_resources',
                'type': 'String'
            }],
            'implementation': {
                'container': {
                    'image':
                        'gcr.io/tfe-ecosystem-dev/temp-custom-job:latest',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        component_factory_function = self._create_a_pytnon_based_component()
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function)

        self.assertDictContainsSubset(custom_job_spec.component_spec.to_dict(),
                                      expected_results)

    def test_run_as_vertex_ai_custom_with_worker_poolspec_container_spec_converts_correctly(
            self):
        component_factory_function = self._create_a_container_based_component()
        worker_pool_spec = [{
            'machine_spec': {
                'machine_type': 'test_machine_type'
            },
            'replica_count': 2,
            'container_spec': {
                'image_uri': 'test_image_uri',
                'command': ['test_command'],
                'args': ['test_args']
            }
        }]

        expected_sub_results = {
            'implementation': {
                'container': {
                    'image':
                        'test_launcher_image',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--payload',
                        '{"display_name": "ContainerComponent", "job_spec": {"worker_pool_specs": [{"machine_spec": {"machine_type": "test_machine_type"}, "replica_count": 2, "container_spec": {"image_uri": "test_image_uri", "command": ["test_command"], "args": ["test_args"]}}], "service_account": "{{$.inputs.parameters[\'service_account}\']}}", "network": "{{$.inputs.parameters[\'network}\']}}", "encryption_spec_key_name": "{{$.inputs.parameters[\'encryption_spec_key_name}\']}}", "tensorboard": "{{$.inputs.parameters[\'tensorboard}\']}}", "base_output_directory": "{{$.inputs.parameters[\'base_output_directory}\']}}"}}',
                        '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function, worker_pool_specs=worker_pool_spec)

        self.assertDictContainsSubset(
            subset=expected_sub_results,
            dictionary=custom_job_spec.component_spec.to_dict())

    def test_run_as_vertex_ai_custom_with_python_package_spec_converts_correctly(
            self):
        component_factory_function = self._create_a_container_based_component()
        python_package_spec = [{'python_package_spec': {'args': ['test_args']}}]

        expected_sub_results = {
            'implementation': {
                'container': {
                    'image':
                        'test_launcher_image',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--payload',
                        '{"display_name": "ContainerComponent", "job_spec": {"worker_pool_specs": [{"python_package_spec": {"args": ["test_args"]}}], "service_account": "{{$.inputs.parameters[\'service_account}\']}}", "network": "{{$.inputs.parameters[\'network}\']}}", "encryption_spec_key_name": "{{$.inputs.parameters[\'encryption_spec_key_name}\']}}", "tensorboard": "{{$.inputs.parameters[\'tensorboard}\']}}", "base_output_directory": "{{$.inputs.parameters[\'base_output_directory}\']}}"}}',
                        '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function, worker_pool_specs=python_package_spec)

        self.assertDictContainsSubset(
            subset=expected_sub_results,
            dictionary=custom_job_spec.component_spec.to_dict())

    def test_run_as_vertex_ai_custom_with_accelerator_type_and_count_converts_correctly(
            self):
        component_factory_function = self._create_a_container_based_component()

        expected_sub_results = {
            'implementation': {
                'container': {
                    'image':
                        'test_launcher_image',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--payload',
                        '{"display_name": "ContainerComponent", "job_spec": {"worker_pool_specs": [{"machine_spec": {"machine_type": "n1-standard-4", "accelerator_type": "test_accelerator_type", "accelerator_count": 2}, "replica_count": 1, "container_spec": {"image_uri": "google/cloud-sdk:latest", "command": ["sh", "-c", "set -e -x\\necho \\"$0, this is an output parameter\\"\\n", "{{$.inputs.parameters[\'input_text\']}}", "{{$.outputs.parameters[\'output_value\'].output_file}}"]}}], "service_account": "{{$.inputs.parameters[\'service_account}\']}}", "network": "{{$.inputs.parameters[\'network}\']}}", "encryption_spec_key_name": "{{$.inputs.parameters[\'encryption_spec_key_name}\']}}", "tensorboard": "{{$.inputs.parameters[\'tensorboard}\']}}", "base_output_directory": "{{$.inputs.parameters[\'base_output_directory}\']}}"}}',
                        '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function,
            accelerator_type="test_accelerator_type",
            accelerator_count=2)

        self.assertDictContainsSubset(
            subset=expected_sub_results,
            dictionary=custom_job_spec.component_spec.to_dict())

    def test_run_as_vertex_ai_custom_with_boot_disk_type_and_size_converts_correctly(
            self):
        component_factory_function = self._create_a_container_based_component()

        expected_sub_results = {
            'implementation': {
                'container': {
                    'image':
                        'test_launcher_image',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--payload',
                        '{"display_name": "ContainerComponent", "job_spec": {"worker_pool_specs": [{"machine_spec": {"machine_type": "n1-standard-4"}, "replica_count": 1, "container_spec": {"image_uri": "google/cloud-sdk:latest", "command": ["sh", "-c", "set -e -x\\necho \\"$0, this is an output parameter\\"\\n", "{{$.inputs.parameters[\'input_text\']}}", "{{$.outputs.parameters[\'output_value\'].output_file}}"]}}, {"machine_spec": {"machine_type": "n1-standard-4"}, "replica_count": "1", "container_spec": {"image_uri": "google/cloud-sdk:latest", "command": ["sh", "-c", "set -e -x\\necho \\"$0, this is an output parameter\\"\\n", "{{$.inputs.parameters[\'input_text\']}}", "{{$.outputs.parameters[\'output_value\'].output_file}}"]}}], "service_account": "{{$.inputs.parameters[\'service_account}\']}}", "network": "{{$.inputs.parameters[\'network}\']}}", "encryption_spec_key_name": "{{$.inputs.parameters[\'encryption_spec_key_name}\']}}", "tensorboard": "{{$.inputs.parameters[\'tensorboard}\']}}", "base_output_directory": "{{$.inputs.parameters[\'base_output_directory}\']}}"}}',
                        '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function, replica_count=2)

        self.assertDictContainsSubset(
            subset=expected_sub_results,
            dictionary=custom_job_spec.component_spec.to_dict())

    def test_run_as_vertex_ai_custom_with_replica_count_greater_than_1_converts_correctly(
            self):
        component_factory_function = self._create_a_container_based_component()

        expected_sub_results = {
            'implementation': {
                'container': {
                    'image':
                        'test_launcher_image',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--payload',
                        '{"display_name": "ContainerComponent", "job_spec": {"worker_pool_specs": [{"machine_spec": {"machine_type": "n1-standard-4"}, "replica_count": 1, "container_spec": {"image_uri": "google/cloud-sdk:latest", "command": ["sh", "-c", "set -e -x\\necho \\"$0, this is an output parameter\\"\\n", "{{$.inputs.parameters[\'input_text\']}}", "{{$.outputs.parameters[\'output_value\'].output_file}}"]}}, {"machine_spec": {"machine_type": "n1-standard-4"}, "replica_count": "1", "container_spec": {"image_uri": "google/cloud-sdk:latest", "command": ["sh", "-c", "set -e -x\\necho \\"$0, this is an output parameter\\"\\n", "{{$.inputs.parameters[\'input_text\']}}", "{{$.outputs.parameters[\'output_value\'].output_file}}"]}}], "service_account": "{{$.inputs.parameters[\'service_account}\']}}", "network": "{{$.inputs.parameters[\'network}\']}}", "encryption_spec_key_name": "{{$.inputs.parameters[\'encryption_spec_key_name}\']}}", "tensorboard": "{{$.inputs.parameters[\'tensorboard}\']}}", "base_output_directory": "{{$.inputs.parameters[\'base_output_directory}\']}}"}}',
                        '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function, replica_count=2)

        self.assertDictContainsSubset(
            subset=expected_sub_results,
            dictionary=custom_job_spec.component_spec.to_dict())

    def test_run_as_vertex_ai_custom_with_time_out_converts_correctly(self):
        component_factory_function = self._create_a_container_based_component()

        expected_sub_results = {
            'implementation': {
                'container': {
                    'image':
                        'test_launcher_image',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--payload',
                        '{"display_name": "ContainerComponent", "job_spec": {"worker_pool_specs": [{"machine_spec": {"machine_type": "n1-standard-4"}, "replica_count": 1, "container_spec": {"image_uri": "google/cloud-sdk:latest", "command": ["sh", "-c", "set -e -x\\necho \\"$0, this is an output parameter\\"\\n", "{{$.inputs.parameters[\'input_text\']}}", "{{$.outputs.parameters[\'output_value\'].output_file}}"]}}], "scheduling": {"timeout": 2}, "service_account": "{{$.inputs.parameters[\'service_account}\']}}", "network": "{{$.inputs.parameters[\'network}\']}}", "encryption_spec_key_name": "{{$.inputs.parameters[\'encryption_spec_key_name}\']}}", "tensorboard": "{{$.inputs.parameters[\'tensorboard}\']}}", "base_output_directory": "{{$.inputs.parameters[\'base_output_directory}\']}}"}}',
                        '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function, timeout=2)

        self.assertDictContainsSubset(
            subset=expected_sub_results,
            dictionary=custom_job_spec.component_spec.to_dict())

    def test_run_as_vertex_ai_custom_with_restart_job_on_worker_restart_converts_correctly(
            self):
        component_factory_function = self._create_a_container_based_component()

        expected_sub_results = {
            'implementation': {
                'container': {
                    'image':
                        'test_launcher_image',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--payload',
                        '{"display_name": "ContainerComponent", "job_spec": {"worker_pool_specs": [{"machine_spec": {"machine_type": "n1-standard-4"}, "replica_count": 1, "container_spec": {"image_uri": "google/cloud-sdk:latest", "command": ["sh", "-c", "set -e -x\\necho \\"$0, this is an output parameter\\"\\n", "{{$.inputs.parameters[\'input_text\']}}", "{{$.outputs.parameters[\'output_value\'].output_file}}"]}}], "scheduling": {"restart_job_on_worker_restart": true}, "service_account": "{{$.inputs.parameters[\'service_account}\']}}", "network": "{{$.inputs.parameters[\'network}\']}}", "encryption_spec_key_name": "{{$.inputs.parameters[\'encryption_spec_key_name}\']}}", "tensorboard": "{{$.inputs.parameters[\'tensorboard}\']}}", "base_output_directory": "{{$.inputs.parameters[\'base_output_directory}\']}}"}}',
                        '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function, restart_job_on_worker_restart=True)

        self.assertDictContainsSubset(
            subset=expected_sub_results,
            dictionary=custom_job_spec.component_spec.to_dict())

    def test_run_as_vertex_ai_custom_with_custom_service_account_converts_correctly(
            self):
        component_factory_function = self._create_a_container_based_component()

        expected_sub_results = {
            'implementation': {
                'container': {
                    'image':
                        'test_launcher_image',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--payload',
                        '{"display_name": "ContainerComponent", "job_spec": {"worker_pool_specs": [{"machine_spec": {"machine_type": "n1-standard-4"}, "replica_count": 1, "container_spec": {"image_uri": "google/cloud-sdk:latest", "command": ["sh", "-c", "set -e -x\\necho \\"$0, this is an output parameter\\"\\n", "{{$.inputs.parameters[\'input_text\']}}", "{{$.outputs.parameters[\'output_value\'].output_file}}"]}}], "service_account": "{{$.inputs.parameters[\'service_account}\']}}", "network": "{{$.inputs.parameters[\'network}\']}}", "encryption_spec_key_name": "{{$.inputs.parameters[\'encryption_spec_key_name}\']}}", "tensorboard": "{{$.inputs.parameters[\'tensorboard}\']}}", "base_output_directory": "{{$.inputs.parameters[\'base_output_directory}\']}}"}}',
                        '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function, service_account='test_service_account')

        self.assertDictContainsSubset(
            subset=expected_sub_results,
            dictionary=custom_job_spec.component_spec.to_dict())

    def test_run_as_vertex_ai_custom_with_display_name_converts_correctly(self):
        component_factory_function = self._create_a_container_based_component()

        expected_sub_results = {
            'implementation': {
                'container': {
                    'image':
                        'test_launcher_image',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--payload',
                        '{"display_name": "test_display_name", "job_spec": {"worker_pool_specs": [{"machine_spec": {"machine_type": "n1-standard-4"}, "replica_count": 1, "container_spec": {"image_uri": "google/cloud-sdk:latest", "command": ["sh", "-c", "set -e -x\\necho \\"$0, this is an output parameter\\"\\n", "{{$.inputs.parameters[\'input_text\']}}", "{{$.outputs.parameters[\'output_value\'].output_file}}"]}}], "service_account": "{{$.inputs.parameters[\'service_account}\']}}", "network": "{{$.inputs.parameters[\'network}\']}}", "encryption_spec_key_name": "{{$.inputs.parameters[\'encryption_spec_key_name}\']}}", "tensorboard": "{{$.inputs.parameters[\'tensorboard}\']}}", "base_output_directory": "{{$.inputs.parameters[\'base_output_directory}\']}}"}}',
                        '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function, display_name='test_display_name')

        self.assertDictContainsSubset(
            subset=expected_sub_results,
            dictionary=custom_job_spec.component_spec.to_dict())

    def test_run_as_vertex_ai_custom_without_container_spec_or_python_package_spec_correctly(
            self):
        component_factory_function = self._create_a_container_based_component()

        worker_pool_spec = [{
            'machine_spec': {
                'machine_type': 'test_machine_type'
            },
            'replica_count': 2
        }]
        with self.assertRaises(ValueError):
            custom_job_spec = custom_job.custom_training_job_op(
                component_factory_function, worker_pool_specs=worker_pool_spec)

    def test_run_as_vertex_ai_custom_with_network_converts_correctly(self):
        component_factory_function = self._create_a_container_based_component()

        expected_sub_results = {
            'implementation': {
                'container': {
                    'image':
                        'test_launcher_image',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--payload',
                        '{"display_name": "ContainerComponent", "job_spec": {"worker_pool_specs": [{"machine_spec": {"machine_type": "n1-standard-4"}, "replica_count": 1, "container_spec": {"image_uri": "google/cloud-sdk:latest", "command": ["sh", "-c", "set -e -x\\necho \\"$0, this is an output parameter\\"\\n", "{{$.inputs.parameters[\'input_text\']}}", "{{$.outputs.parameters[\'output_value\'].output_file}}"]}}], "service_account": "{{$.inputs.parameters[\'service_account}\']}}", "network": "{{$.inputs.parameters[\'network}\']}}", "encryption_spec_key_name": "{{$.inputs.parameters[\'encryption_spec_key_name}\']}}", "tensorboard": "{{$.inputs.parameters[\'tensorboard}\']}}", "base_output_directory": "{{$.inputs.parameters[\'base_output_directory}\']}}"}}',
                        '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function, network='test_network')

        self.assertDictContainsSubset(
            subset=expected_sub_results,
            dictionary=custom_job_spec.component_spec.to_dict())

    def test_run_as_vertex_ai_custom_with_labels_converts_correctly(self):
        component_factory_function = self._create_a_container_based_component()

        expected_sub_results = {
            'implementation': {
                'container': {
                    'image':
                        'test_launcher_image',
                    'command': [
                        'python3', '-u', '-m',
                        'google_cloud_pipeline_components.experimental.remote.gcp_launcher.launcher'
                    ],
                    'args': [
                        '--type', 'CustomJob', '--payload',
                        '{"display_name": "ContainerComponent", "job_spec": {"worker_pool_specs": [{"machine_spec": {"machine_type": "n1-standard-4"}, "replica_count": 1, "container_spec": {"image_uri": "google/cloud-sdk:latest", "command": ["sh", "-c", "set -e -x\\necho \\"$0, this is an output parameter\\"\\n", "{{$.inputs.parameters[\'input_text\']}}", "{{$.outputs.parameters[\'output_value\'].output_file}}"]}}], "labels": {"test_key": "test_value"}, "service_account": "{{$.inputs.parameters[\'service_account}\']}}", "network": "{{$.inputs.parameters[\'network}\']}}", "encryption_spec_key_name": "{{$.inputs.parameters[\'encryption_spec_key_name}\']}}", "tensorboard": "{{$.inputs.parameters[\'tensorboard}\']}}", "base_output_directory": "{{$.inputs.parameters[\'base_output_directory}\']}}"}}',
                        '--project', {
                            'inputValue': 'project'
                        }, '--location', {
                            'inputValue': 'location'
                        }, '--gcp_resources', {
                            'outputPath': 'gcp_resources'
                        }
                    ]
                }
            }
        }
        custom_job_spec = custom_job.custom_training_job_op(
            component_factory_function, labels={"test_key": "test_value"})

        self.assertDictContainsSubset(
            subset=expected_sub_results,
            dictionary=custom_job_spec.component_spec.to_dict())
