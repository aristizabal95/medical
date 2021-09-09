"""MLCube handler file"""
import os
import typer
import subprocess


app = typer.Typer()


class EvaluateTask(object):
    """Runs evaluation metrics given the predictions and label files

    Args:
        object ([type]): [description]
    """

    @staticmethod
    def run(
        labels_csv: str, preds_csv: str, parameters_file: str, output_file: str
    ) -> None:
        cmd = f"python3 metrics.py --labels_csv={labels_csv} --preds_csv={preds_csv} --parameters_file={parameters_file} --output_file={output_file}"
        splitted_cmd = cmd.split()

        process = subprocess.Popen(splitted_cmd, cwd=".")
        process.wait()


@app.command("evaluate")
def evaluate(
    labels_csv: str = typer.Option(..., "--labels_csv"),
    preds_csv: str = typer.Option(..., "--preds_csv"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
):
    output_file = os.path.join(output_path, "results.yaml")
    EvaluateTask.run(labels_csv, preds_csv, parameters_file, output_file)


@app.command("test")
def test():
    pass


if __name__ == "__main__":
    app()
