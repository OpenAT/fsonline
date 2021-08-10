from invoke import task


@task
def reset(git_repo_dir, branch_or_tag=None):
    """ Will completely reset the git repository and clean all unknown files """
