import fire

class Start:
    """Package manager based on pip and venv
    """
    def new(self, project_name):
        """Create a new project
        Args:
            project_name: name of the project
        """
        print(project_name)
        return self


def main():
    fire.Fire(Start)


if __name__ == '__main__':
    main()