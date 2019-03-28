$authorizedKeyPath = "C:\users\root\.ssh\authorized_keys"
$acl = Get-Acl $authorizedKeyPath
$ar = New-Object System.Security.AccessControl.FileSystemAccessRule("NT Service\sshd", "Read", "Allow")
$acl.SetAccessRule($ar)
Set-Acl $authorizedKeyPath $acl