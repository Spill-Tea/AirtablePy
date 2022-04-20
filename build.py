"""Simple Build Script to create a python package wheel. """

# Python Dependencies
import os
import shutil
import subprocess


project_dir = os.path.split(os.path.abspath(__file__))[0]
package_name = "AirtablePy"


def main():
    # Cleanup before build
    try:
        shutil.rmtree('dist')
    except FileNotFoundError:
        pass
    try:
        shutil.rmtree('build')
    except FileNotFoundError:
        pass
    try:
        shutil.rmtree(f'{package_name}/{package_name}.egg-info')
    except FileNotFoundError:
        pass

    # Build
    subprocess.run(["python", "setup.py", "sdist", "bdist_wheel"])

    # Cleanup after
    shutil.rmtree('build')
    shutil.rmtree(f'{package_name}.egg-info')
    dist_path = os.path.join(project_dir, 'dist')
    non_wheels = [os.path.join(dist_path, f)
                  for f in os.listdir(dist_path)
                  if os.path.splitext(f)[-1] != '.whl']
    for fp in non_wheels:
        os.remove(fp)


if __name__ == '__main__':
    main()
