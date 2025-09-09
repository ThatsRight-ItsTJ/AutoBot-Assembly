class ProjectMetadata:
    def __init__(self, name, path, files, size, language, description):
        self.name = name
        self.path = path
        self.files = files
        self.size = size
        self.language = language
        self.description = description

class ProjectGenerator:
    async def generate_project(self, project_name, output_dir, files, project_description, language):
        import os
        import json

        project_path = os.path.join(output_dir, project_name)
        os.makedirs(project_path, exist_ok=True)

        for file_name, content in files.items():
            file_path = os.path.join(project_path, file_name)
            with open(file_path, 'w') as f:
                f.write(content)

        metadata = {
            'name': project_name,
            'path': project_path,
            'files': list(files.keys()),
            'size': sum(len(content) for content in files.values()),
            'language': language,
            'description': project_description
        }

        metadata_path = os.path.join(project_path, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)

        return ProjectMetadata(**metadata)