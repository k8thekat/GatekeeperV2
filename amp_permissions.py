'''
   Copyright (C) 2021-2022 Katelynn Cadwallader.

   This file is part of Gatekeeper, the AMP Minecraft Discord Bot.

   Gatekeeper is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3, or (at your option)
   any later version.

   Gatekeeper is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
   or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
   License for more details.

   You should have received a copy of the GNU General Public License
   along with Gatekeeper; see the file COPYING.  If not, write to the Free
   Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
   02110-1301, USA. 
'''


from typing import TYPE_CHECKING, TypedDict, Union

if TYPE_CHECKING:
    from amp_instance import AMP_Instance
    from amp_ads import AMP_ADS


def perms_super():
    core = ['Core.*',
            'Core.RoleManagement.*',
            'Core.UserManagement.*',
            '-Core.Scheduler.*',
            '-Core.AuditLog.*',
            '-Core.RoleManagement.DeleteRoles',
            '-Core.RoleManagement.CreateCommonRoles',
            '-Core.UserManagement.UpdateUserInfo',
            '-Core.UserManagement.UpdateOwnAccount',
            '-Core.UserManagement.DeleteUser',
            '-Core.UserManagement.ResetUserPassword',
            '-Core.UserManagement.CreateNewUser',
            '-Core.UserManagement.ViewOtherUsersSessions',
            '-Core.UserManagement.EndUserSessions',
            'Core.UserManagement.ViewUserInfo',
            'Instances.*',
            'ADS.*',
            '-ADS.TemplateManagement.*',
            'Settings.*',
            '-Settings.GSMyAdmin.*',
            '-Settings.ADSModule.*',
            '-Settings.FileManagerPlugin.*',
            '-Settings.EmailSenderPlugin.*',
            '-Settings.WebRequestPlugin.*',
            '-Settings.LocalFileBackupPlugin.*',
            '-Settings.steamcmdplugin.*',
            'ADS.InstanceManagement.*',
            '-ADS.InstanceManagement.RegisterToController',
            '-ADS.InstanceManagement.CreateInstance',
            '-ADS.InstanceManagement.SuspendInstances',
            '-ADS.InstanceManagement.UpgradeInstances',
            '-ADS.InstanceManagement.DeleteInstances',
            '-ADS.InstanceManagement.AttachRemoteADSInstance',
            '-ADS.InstanceManagement.RemoveRemoteADSInstance',
            '-ADS.InstanceManagement.EditRemoteTargets',
            '-ADS.InstanceManagement.Convert',
            '-ADS.InstanceManagement.Reconfigure',
            '-ADS.InstanceManagement.RefreshConfiguration',
            '-ADS.InstanceManagement.RefreshRemoteConfigStores',
            'FileManager.*',
            '-FileManager.FileManager.CreateArchive',
            '-FileManager.FileManager.ExtractArchive',
            '-FileManager.FileManager.ChangeBackupExclusions',
            '-FileManager.FileManager.ConnectViaSFTP',
            '-FileManager.FileManager.ModifyAMPConfigFiles',
            '-FileManager.FileManager.DownloadFromURL',
            'LocalFileBackup.*',
            '-LocalFileBackup.Backup.ViewBackupsList',
            '-LocalFileBackup.Backup.DeleteBackup',
            '-LocalFileBackup.Backup.RestoreBackup',
            '-LocalFileBackup.Backup.ToggleStickiness',
            'Core.AppManagement.*',
            '-Core.AppManagement.UpdateApplication',
            '-Core.Special.*']
    return core


async def setup_Gatekeeper_role(instance: Union[AMP_ADS, AMP_Instance]):
    """Creates the `Gatekeeper` role, Adds us to the Membership of that Role and sets its AMP permissions."""
    instance._logger.warning('Creating the AMP role `Gatekeeper`...')
    await instance.createRole('Gatekeeper')
    await set_roleID(instance=instance)
    instance.AMPUSER_id = get_userID(instance=instance, name=instance.AMPUSER)
    if instance.AMPUSER_id != False:
        await instance.setAMPUserRoleMembership(instance.AMPUSER_id, instance._roleID, True)
        instance._logger.warning(f'***ATTENTION*** Adding {instance.AMPUSER} to `Gatekeeper` Role.')
        await setup_Gatekeeper_permissions()


async def setup_Gatekeeper_permissions(instance: Union[AMP_ADS, AMP_Instance]):
    """Sets the Permissions Nodes for AMP Gatekeeper Role"""
    instance._logger.info('Setting AMP Role Permissions for `Gatekeeper`...')
    core = perms_super()
    for perm in core:
        enabled = True
        if perm.startswith('-'):
            enabled = False
            perm = perm[1:]
        if await instance.setAMPRolePermissions(instance._roleID, perm, enabled):
            instance._logger.warning(f'Set __{perm}__ for _Gatekeeper_ to `{enabled}` on {instance.FriendlyName if instance.InstanceID != 0 else "AMP"}')


async def check_Gatekeeper_rolePermissions(instance: Union[AMP_ADS, AMP_Instance]) -> bool:
    """- Will check `Gatekeeper Role` for `Permission Nodes` when we have `Super Admin` and `not InstanceID = 0`.\n
    - Checks for `Gatekeeper Role`, if we `have the Gatekeeper Role` and `Super Admin Role`
    Returns `True` if we have permissions. Otherwise `False`"""
    # If we have Super Admin; lets check for the Bot Role and if we are not on the Main Instance.
    failed = False

    results = await instance.getAMPUserInfo(name=instance.AMPUSER)
    if "result" in results:
        instance.AMPUSER_info = results["results"]

        if "ID" in results["results"]:
            instance.AMPUSER_id = instance.AMPUSER_info['ID']  # This gets my AMP User Information
    await set_roleID(instance=instance)

    # `Gatekeeper Role inside of AMP`
    if instance._roleID != None:
        # self.logger.dev('Gatekeeper Role Exists..')
        instance._role_exists = True

    # Gatekeeper has `Gatekeeper` Role inside of AMP
    if instance._role_exists and instance._roleID in instance.AMPUSER_info['Roles']:
        # self.logger.dev('Gatekeeper User has Gatekepeer Role.')
        instance._role_exists = True

    # `Super_Admin Role inside of AMP`
    if instance.SUPERADMIN_roleID in instance.AMPUSER_info['Roles']:
        # self.logger.dev('Gatekeeper User has Super Admins')
        instance._have_superAdmin = True

    if instance._role_exists:
        instance._logger.info(f'Checking `Gatekeeper Role` permissions on {"AMP" if instance.InstanceID == 0 else instance.FriendlyName}')
        for perm in instance._perms:
            # Skip the perm check on ones we "shouldn't have!"
            if perm.startswith('-'):
                continue

            role_perms = await instance.getAMPRolePermissions(instance._roleID)

            if perm not in role_perms['result']:
                if instance._have_superAdmin:
                    instance._logger.warning()(f'We have `Super Admins` Role and we are missing Permissions, returning to setup Permissions.')
                    return False

                else:
                    end_point = instance.AMPURL.find(":", 5)
                    instance._logger.warning(f'Gatekeeper is missing the permission __{perm}__ Please visit {instance.AMPURL[:end_point]}:{instance.Port} under Configuration -> Role Management -> Gatekeeper')
                failed = True

        if not failed:
            return True
    else:
        return False


async def get_userID(instance: Union[AMP_ADS, AMP_Instance], name: str) -> Union[str, bool]:
    """Returns AMP Users ID Only."""
    result = await instance.getAMPUserInfo(name=name)
    if "result" in result and "ID" in result:
        return result['result']['ID']
    else:
        return result


async def set_roleID(instance: Union[AMP_ADS, AMP_Instance]):
    """Gets a list of the Instances Roles and interates through them looking for `Gatekeeper` role.

    Sets `_roleID` = Gatekeeper Role ID"""
    roles: dict[str, str] = await instance.getRoleIds()
    for role in roles:
        if roles[role].lower() == 'gatekeeper':
            instance._roleID = role
            if instance.InstanceID == 0:
                instance._logger.warning(f'Found Gatekeeper Role - ID: {instance._roleID}')


async def set_SuperAdmin_roleID(instance: Union[AMP_ADS, AMP_Instance]):
    roles = await instance.getRoleIds()
    for role in roles:
        if roles[role].lower() == 'super admins':
            instance.SUPERADMIN_roleID = role
            if instance.InstanceID == 0:
                instance._logger.warning(f'Found Super Admin Role - ID: {instance.SUPERADMIN_roleID}')


async def check_SessionPermissions(instance: Union[AMP_ADS, AMP_Instance]) -> bool:
    """These check AMP for the proper Permission Nodes.\n
    Returns `True` only if I have ALL the Required Permissions; Otherwise `False`."""
    instance._logger.warning(f'Checking Session: {instance._session_id} for proper permissions...')
    failed = False
    for perm in instance._perms:
        # Skip the perm check on ones we "shouldn't have!"
        if perm.startswith('-'):
            continue

        check = await instance.currentSessionHasPermission(perm)

        # self._logger.dev(f'Session {"has" if check else "is missing" } permisson node: {perm}')
        if check:
            continue

        if instance.Module == 'AMP':  # AKA the main (InstanceID == 0)
            instance._logger.warning(f'Gatekeeper is missing the permission __{perm}__ Please check under Configuration -> User Management for {instance.AMPUSER}.')

        else:
            end_point = instance.AMPURL.find(":", 5)
            instance._logger.warning(f'Gatekeeper is missing the permission __{perm}__ Please visit {instance.AMPURL[:end_point]}:{instance.Port} under Configuration -> Role Management -> Gatekeeper')
        failed = True

    if failed:
        instance._logger.critical(f'***ATTENTION*** The Bot is missing permissions, some or all functionality may not work properly!')
        # Please see this image for the required bot user Permissions **(Github link to AMP Basic Perms image here)**
        return check

    return True
