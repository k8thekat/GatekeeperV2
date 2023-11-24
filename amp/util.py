from API import AMP_API


async def getNodespec(amp: AMP_API) -> list[str]:
    """
    Returns a list of ADS Config nodes.

    Args:
        amp (AMP_API): AMP API class object.
    Returns:
        list : Returns a list of all known nodes for a Server/Instance.\n
    *Node List (NOT INCLUSIVE)*\n
    `GSMyAdmin.WebserverSettings.EnableWebSockets
    GSMyAdmin.WebserverSettings.EnableFetchPostEndpoints
    GSMyAdmin.WebserverSettings.APIRateLimit
    GSMyAdmin.WebserverSettings.AllowGETForAPIEndpoints
    GSMyAdmin.WebserverSettings.CORSOrigin
    GSMyAdmin.WebserverSettings.DisableCompression
    GSMyAdmin.GSMyAdminSettings.ScheduleOffsetSeconds
    GSMyAdmin.GSMyAdminSettings.AppStartupMode
    GSMyAdmin.GSMyAdminSettings.FirstStart
    GSMyAdmin.GSMyAdminSettings.ShutdownProperly
    GSMyAdmin.GSMyAdminSettings.SafeMode
    GSMyAdmin.GSMyAdminSettings.PreviousVersion
    GSMyAdmin.GSMyAdminSettings.StoreIPAddressesAsMACAddresses
    GSMyAdmin.GSMyAdminSettings.MapAllPluginStores
    GSMyAdmin.GSMyAdminSettings.Theme
    GSMyAdmin.GSMyAdminSettings.ShowHelpOnStatus
    GSMyAdmin.BrandingSettings.DisplayBranding
    GSMyAdmin.BrandingSettings.PageTitle
    GSMyAdmin.BrandingSettings.CompanyName
    GSMyAdmin.BrandingSettings.WelcomeMessage
    GSMyAdmin.BrandingSettings.BrandingMessage
    GSMyAdmin.BrandingSettings.ShortBrandingMessage
    GSMyAdmin.BrandingSettings.URL
    GSMyAdmin.BrandingSettings.SupportURL
    GSMyAdmin.BrandingSettings.SupportText
    GSMyAdmin.BrandingSettings.SubmitTicketURL
    GSMyAdmin.BrandingSettings.LogoURL
    GSMyAdmin.BrandingSettings.BackgroundURL
    GSMyAdmin.BrandingSettings.SplashFrameURL
    GSMyAdmin.BrandingSettings.ForgotPasswordURL
    LocalFileBackupPlugin.CloudStorageSettings.UseS3Storage
    LocalFileBackupPlugin.CloudStorageSettings.S3ServiceURL
    LocalFileBackupPlugin.CloudStorageSettings.S3AuthenticationRegion
    LocalFileBackupPlugin.CloudStorageSettings.S3BucketName
    LocalFileBackupPlugin.CloudStorageSettings.S3AccessKey
    LocalFileBackupPlugin.CloudStorageSettings.S3SecretKey
    LocalFileBackupPlugin.CloudStorageSettings.S3UploadMode
    EmailSenderPlugin.SMTPSettings.UseSSL
    EmailSenderPlugin.SMTPSettings.Host
    EmailSenderPlugin.SMTPSettings.Port
    EmailSenderPlugin.SMTPSettings.Username
    EmailSenderPlugin.SMTPSettings.Password
    EmailSenderPlugin.SMTPSettings.EmailFrom
    WebRequestPlugin.WebhookLoginSettings.PushbulletAccessToken
    FileManagerPlugin.FileManagerSettings.BasePath
    FileManagerPlugin.FileManagerSettings.AdditionalVirtualDirectories
    FileManagerPlugin.FileManagerSettings.FastFileTransfers
    ADSModule.ADSSettings.AutoReactivate
    ADSModule.ADSSettings.Mode
    ADSModule.ADSSettings.AutostartInstances
    ADSModule.ADSSettings.InstanceStartDelay
    ADSModule.ADSSettings.IgnoreCompatibility
    ADSModule.ADSSettings.ConfigurationRepositories
    ADSModule.ADSSettings.ShowDeprecated
    GSMyAdmin.LoginSettings.UseAuthServer
    GSMyAdmin.LoginSettings.AuthServerURL
    GSMyAdmin.MonitoringSettings.UseMulticoreCPUCalc
    GSMyAdmin.MonitoringSettings.IgnoreSMTCores
    GSMyAdmin.MonitoringSettings.ConsoleScrollback
    GSMyAdmin.MonitoringSettings.FullMetricsGathering
    GSMyAdmin.MonitoringSettings.ReportPhysicalMemoryAsTotal
    GSMyAdmin.MonitoringSettings.MetricsPollInterval
    ADSModule.Networking.DefaultIPBinding
    ADSModule.Networking.DefaultAppIPBinding
    ADSModule.Networking.DockerExternalIPBinding
    ADSModule.Networking.AMPPortRanges
    ADSModule.Networking.PortAssignment
    ADSModule.Networking.AppPortRanges
    ADSModule.Networking.AppPortExclusions
    ADSModule.Networking.MetricsServerPort
    ADSModule.Networking.UseDockerHostNetwork
    ADSModule.Networking.UseTraefik
    ADSModule.Networking.TraefikNetworkName
    ADSModule.Networking.TraefikDomainWildcard
    ADSModule.Networking.AccessMode
    ADSModule.Networking.BaseURL
    ADSModule.NewInstanceDefaults.NewInstanceKey
    ADSModule.NewInstanceDefaults.DefaultSettings
    ADSModule.NewInstanceDefaults.DefaultReleaseStream
    ADSModule.NewInstanceDefaults.UseDocker
    ADSModule.NewInstanceDefaults.CreateAsShared
    ADSModule.NewInstanceDefaults.DefaultAuthServerURL
    ADSModule.NewInstanceDefaults.PropagateAuthServer
    ADSModule.NewInstanceDefaults.UseOverlays
    ADSModule.NewInstanceDefaults.OverlayPath
    ADSModule.NewInstanceDefaults.MatchVersion
    ADSModule.NewInstanceDefaults.DefaultPostCreate
    ADSModule.NewInstanceDefaults.ExcludeFromFirewall
    ADSModule.ServiceLimits.InstanceLimit
    ADSModule.ServiceLimits.CreateLocalInstances
    LocalFileBackupPlugin.BackupLimits.MaxTotalSizeMB
    LocalFileBackupPlugin.BackupLimits.MaxIndividualSizeMB
    LocalFileBackupPlugin.BackupLimits.MaxBackupCount
    LocalFileBackupPlugin.BackupLimits.ReplacePolicy
    LocalFileBackupPlugin.BackupLimits.Compression
    GSMyAdmin.SecuritySettings.EnablePassthruAuth
    GSMyAdmin.SecuritySettings.AuthFailureTimeWindow
    GSMyAdmin.SecuritySettings.AuthFailureAttemptsInWindow
    GSMyAdmin.SecuritySettings.TwoFactorMode
    GSMyAdmin.SecuritySettings.RequireSessionIPStickiness
    GSMyAdmin.PrivacySettings.PrivacySettingsSet
    GSMyAdmin.PrivacySettings.AutoReportFatalExceptions
    GSMyAdmin.PrivacySettings.AllowAnalytics
    FileManagerPlugin.SecuritySettings.RestrictUploadExtensions
    FileManagerPlugin.SecuritySettings.RestrictDownloadExtensions
    FileManagerPlugin.SecuritySettings.DownloadableExtensions
    FileManagerPlugin.SecuritySettings.UploadableExtensions
    FileManagerPlugin.SecuritySettings.AllowExtensionChange
    FileManagerPlugin.SecuritySettings.AllowArchiveOperations
    FileManagerPlugin.SecuritySettings.OnlyExtractUploadableExtensionsFromArchives
    FileManagerPlugin.SecuritySettings.HoneypotSFTPLogins
    FileManagerPlugin.SFTPServerSettings.SFTPEnabled
    FileManagerPlugin.SFTPServerSettings.SFTPPortNumber
    FileManagerPlugin.SFTPServerSettings.EnableCompression
    steamcmdplugin.SteamWorkshopSettings.WorkshopItemIDs
    steamcmdplugin.SteamCMDUpdateSettings.AutomaticallyRetryOnFailure
    steamcmdplugin.SteamCMDUpdateSettings.AutomaticRetryLimit
    steamcmdplugin.SteamCMDUpdateSettings.UpdateCheckMethod
    steamcmdplugin.SteamCMDUpdateSettings.SteamCMDBetaPassword
    steamcmdplugin.SteamCMDUpdateSettings.ThrottleDownloadSpeed
    steamcmdplugin.SteamCMDUpdateSettings.KeepSteamCMDScripts`
    """
    nodes: list = []
    amp = AMP_API(url=amp._url, amp_user=amp._amp_user, amp_password=amp._amp_password)
    res = await amp.getSettingsSpec()

    if type(res) != dict or "result" not in res:
        return nodes

    res = res["result"]
    for key in res:
        for value in res[key]:
            for entry in value:
                if entry.lower() == "node":
                    nodes.append(value[entry])
    return nodes
