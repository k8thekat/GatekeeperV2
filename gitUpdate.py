import git
import sys
import os
import logging

#Custom Scripts
import bot_config

bot_version = ''

def init(version = str):
    global logger,bot_version
    bot_version = version
    logger = logging.getLogger(__name__)
    githubUpdate()

def githubUpdate():
    logger.info('Git Update in Progress...')
    try:
        repo = git.Repo(os.getcwd())
    except Exception as e:
        logger.error(f'You are not currently using a Repo...{e}')
        return
    logger.info('You are currently set to branch: {config.gitrepo_branch}, checking for updates on GitHub...')
    commits = list(repo.iter_commits(bot_config.gitrepo_branch,max_count = 5))
    update = commits[0].hexsha #This accesses the most recent commit HEXSHA value of the specified branch
    current_branch = repo.head.reference #This accesses the current files brand head which gives me access to the HEXSHA
    current = current_branch.commit.hexsha
    phrase = ''

    if update == current:
        phrase = f'The Keymaster says you are up to date. Ver: {bot_version} Hexsha: {current}.'
        logger.info(f'The Keymaster says you are up to date. Ver: {bot_version} Hexsha: {current}.')
        return phrase

    if update != current and bot_config.gitAutoUpdate:
        logger.info('Current Version:',current,'Version on gitHub:',update,'\nLets download our update...')

        to_update = repo.remotes.origin
        to_update.pull(bot_config.gitrepo_branch) #Can pass in the branch name.

        logger.info('Restarting the bot, please wait...')
        sys.stdout.flush()
        os.execv(sys.executable, ['python3'] + sys.argv)

    if update != current and not bot_config.gitAutoUpdate:
        phrase = f'The Keymaster says you have an update on GitHub!, but you have Auto Update turned off.'
        logger.info('Gatekeeper has an update on gitHub!')
        
        for index in range(0,len(commits)):
            if commits[index].hexsha == current:
                if index == 1:
                    logger.warning(f'Gatekeeper is currently {index} commit behind, please consider updating!')
                else:
                    logger.warning(f'Gatekeeper is currently {index} commits behind, please consider updating!')
            else:
                logger.warning('Gatekeeper is more than 5 commits behind! Please consider updating!!!')
            return