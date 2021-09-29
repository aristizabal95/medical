import requests
import yaml
import os
from shutil import copyfile

from medperf.utils import pretty_error, get_file_sha1, cube_path
from medperf.config import config


class Server:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.token = None

    def login(self, username: str, password: str):
        """Authenticates the user with the server. Required for most endpoints

        Args:
            username (str): Username
            password (str): Password
        """
        body = {"username": username, "password": password}
        res = requests.post(f"{self.server_url}/auth-token/", json=body)
        if res.status_code != 200:
            pretty_error("Unable to authentica user with provided credentials")

        self.token = res.json()["token"]

    def __auth_get(self, url, **kwargs):
        return self.__auth_req(url, requests.get, **kwargs)

    def __auth_post(self, url, **kwargs):
        return self.__auth_req(url, requests.post, **kwargs)

    def __auth_req(self, url, req_func, **kwargs):
        if self.token is None:
            pretty_error("Must be authenticated")
        return req_func(url, headers={"Authorization": f"Token {self.token}"}, **kwargs)

    def get_benchmark(self, benchmark_uid: int) -> dict:
        """Retrieves the benchmark specification file from the server

        Args:
            benchmark_uid (int): uid for the desired benchmark

        Returns:
            dict: benchmark specification
        """
        res = self.__auth_get(f"{self.server_url}/benchmarks/{benchmark_uid}")
        if res.status_code != 200:
            pretty_error("the specified benchmark doesn't exist")
        benchmark = res.json()
        return benchmark

    def get_benchmark_models(self, benchmark_uid: int) -> list[int]:
        """Retrieves all the models associated with a benchmark. reference model not included

        Args:
            benchmark_uid (int): UID of the desired benchmark

        Returns:
            list[int]: List of model UIDS
        """
        res = self.__auth_get(f"{self.server_url}/benchmarks/{benchmark_uid}/models")
        if res.status_code != 200:
            pretty_error("couldn't retrieve models for the specified benchmark")
        models = res.json()
        model_uids = [model["id"] for model in models]
        return model_uids

    def get_cube_metadata(self, cube_uid: int) -> dict:
        """Retrieves metadata about the specified cube

        Args:
            cube_uid (int): UID of the desired cube.

        Returns:
            dict: Dictionary containing url and hashes for the cube files
        """
        res = self.__auth_get(f"{self.server_url}/mlcubes/{cube_uid}/")
        if res.status_code != 200:
            pretty_error("the specified cube doesn't exist")
        metadata = res.json()
        return metadata

    def get_cube(self, url: str, cube_uid: int) -> str:
        """Downloads and writes an mlcube.yaml file from the server

        Args:
            url (str): URL where the mlcube.yaml file can be downloaded.
            cube_uid (int): Cube UID.

        Returns:
            str: location where the mlcube.yaml file is stored locally.
        """
        cube_file = config["cube_filename"]
        return self.__get_cube_file(url, cube_uid, "", cube_file)

    def get_cube_params(self, url: str, cube_uid: int) -> str:
        """Retrieves the cube parameters.yaml file from the server

        Args:
            url (str): URL where the parameters.yaml file can be downloaded.
            cube_uid (int): Cube UID.

        Returns:
            str: Location where the parameters.yaml file is stored locally.
        """
        ws = config["workspace_path"]
        params_file = config["params_filename"]
        return self.__get_cube_file(url, cube_uid, ws, params_file)

    def get_cube_additional(self, url: str, cube_uid: int) -> str:
        """Retrieves and stores the additional_files.tar.gz file from the server

        Args:
            url (str): URL where the additional_files.tar.gz file can be downloaded.
            cube_uid (int): Cube UID.

        Returns:
            str: Location where the additional_files.tar.gz file is stored locally.
        """
        add_path = config["additional_path"]
        tball_file = config["tarball_filename"]
        return self.__get_cube_file(url, cube_uid, add_path, tball_file)

    def __get_cube_file(self, url: str, cube_uid: int, path: str, filename: str):
        res = requests.get(url)
        if res.status_code != 200:
            pretty_error("There was a problem retrieving the specified file at " + url)

        c_path = cube_path(cube_uid)
        path = os.path.join(c_path, path)
        if not os.path.isdir(path):
            os.makedirs(path)
        filepath = os.path.join(path, filename)
        open(filepath, "wb+").write(res.content)
        return filepath

    def upload_dataset(self, reg_dict: dict):
        """Uploads registration data to the server, under the sha name of the file.

        Args:
            reg_dict (dict): Dictionary containing registration information.
        """
        res = self.__auth_post(f"{self.server_url}/datasets/", json=reg_dict)
        if res.status_code != 201:
            pretty_error("Could not upload the dataset")
        return res.json()["id"]

    def upload_results(self, results_dict: dict) -> int:
        """Uploads results to the server.

        Args:
            results_dict (dict): Dictionary containing results information.
        """
        res = self.__auth_post(f"{self.server_url}/results/", json=results_dict)
        if res.status_code != 201:
            pretty_error("Could not upload the results")
        return res.json()["id"]
