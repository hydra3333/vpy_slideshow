Option Explicit

Const maxNumbers = 6

Dim srcExt
srcExt = lcase(".bmp,.gif,.jpg,.jpeg,.tif,.tiff,.avi,.wmv,.asf,.mpg,.mpeg,.flv,.swf,.3gp,.mov,.mp4,.flv,.vob,.mkv,.vob,.pdf,.mp3,.wav,.m4a,")  ' always have a trailing comma in this string

Dim colNArgs, colUArgs, objArg
Dim fso, fldr, fx
Dim n , ii
Dim relFldr
ReDim dcwF(10000)
ReDim dcwFnew(10000)

'Check for right WSH version
'If WScript.Version <> "5.8" Then 
'   msgbox "Wscript version incorrect " & WScript.Version 
'   Wscript.Quit
'End If

'-------------------------------------------------------
'msgbox "wscript.arguments.Unnamed.Count=" & wscript.arguments.Unnamed.Count
'tmp=""
'If wscript.arguments.Unnamed.Count >= 0  Then
'	for i=0 to wscript.arguments.Unnamed.Count-1
'		tmp=tmp & i 
'		tmp=tmp & "=<" 
'		tmp=tmp & Wscript.Arguments.Item(i) 
'		tmp=tmp & "> "
'	next
'end if
'msgbox tmp
'Wscript.Quit
'-------------------------------------------------------

'Gather arguments passed
Set colNArgs = WScript.Arguments.Named
Set colUArgs = WScript.Arguments.UnNamed
If colNArgs.Count = 0 AND colUArgs.Count = 0 Then Wscript.Quit

'Enumerate Named Arguments
If colNArgs.Count > 0 Then
	If colNArgs.Exists("?") Then ShowHelp
End If

Set fso = CreateObject("Scripting.FileSystemObject")

'Enumerate paths
n=0
If colUArgs.Count > 0 Then
	For Each objArg in colUArgs
		Set fldr = fso.GetFolder(objArg)
		If lcase(left(fldr,2)) = lcase("C:") then
			wscript.echo "Sorry, will not operate on the C: drive for safety reasons... " & fldr
		Else
			relFldr = fldr
			RecursivelyFind fldr 
		End If
	Next
End If
ReDim Preserve dcwF(n)
ReDim Preserve dcwFnew(n)

'Dim txtFileName, tsFile
'txtFileName = "c:\temp\dcwDirlist.txt"
'Set tsFile = fso.OpenTextFile(txtFileName, 2, True, -2)
'tsFile.WriteLine "Dump of " & n & " renames"
'for ii=1 to n
'	tsFile.WriteLine "<" & dcwF(ii) & "> <" & dcwFnew(ii) & ">"
'next
'tsFile.WriteLine "Starting renames"
for ii=1 to n
	'tsFile.WriteLine ii & "About to rename <" & dcwF(ii) & "> to <" & dcwFnew(ii) & ">"

	'WScript.StdOut.WriteLine(ii & " In rename loop, About to rename <" & dcwF(ii) & "> to <" & dcwFnew(ii) & ">")
	set fx = fso.GetFile(dcwF(ii))
	fx.name = dcwFnew(ii)
	set fx = Nothing
next
'tsFile.Close

Set fldr = Nothing
Set fso = Nothing
wscript.echo "done " & n
Wscript.Quit

'-----------------------------------------------------
Public Sub RecursivelyFind(ByRef fldr)
   dim subfolders,files,folder,file, ext, newname

   Set subfolders = fldr.SubFolders
   Set files = fldr.Files

   'Display the path and all of the folders.
'   Wscript.Echo "---Folders--- in " & fldr.Path
'   For Each folder in subfolders
'      Wscript.Echo folder.Name
'   Next
 
   'Display all of the files.
'   Wscript.Echo "---Files--- in " & fldr.Path
   For Each file in files
'''	wscript.echo n & " " & file.path & " parentfolder " & file.ParentFolder
'''	Wscript.Quit
	ext = "." & fso.GetExtensionName(file.name) & ","
	If instr(srcExt, lcase(ext)) > 0 then '<<<<<<<<<<<<---------------
'		wscript.echo file.name 
		n = n + 1
		If n > UBound(dcwF) Then 
			ReDim Preserve dcwF(n+2000)
			ReDim Preserve dcwFnew(n+2000)
		End if
		dcwF(n) = file.ParentFolder & "\" & file.name
'*******************************************************************
		Call NewNameForTheFile(file,newname)
'*******************************************************************
'		dcwFnew(n) = file.ParentFolder & "\" & newname
		dcwFnew(n) = newname
'		wscript.echo n & " " & dcwF(n) & " " & dcwFnew(n)
	End If
   Next  

   'Recurse all of the subfolders.
   For Each folder in subfolders
      RecursivelyFind  folder
   Next  

   'Cleanup current recursion level
   Set subfolders = Nothing
   Set files = Nothing
End Sub
'-----------------------------------------------------
Sub ShowHelp()
	msgbox "ThisScript.vbs [/?] [Path, [...]]" & Chr(34) & " path   - Directory, comma separated values" 
	Wscript.Quit
End Sub
'-----------------------------------------------------
Sub NewNameForTheFile(fi,resultname)
Dim thePath, folderprefix, theFilename, theExt, tmp, prefix, before, after
	thePath = lcase(fi.Path)
	folderprefix = RightFolderName(thePath)		' IN THIS SCRIPT, WE ONLY USE THE BOTTOM FOLDERNAME OCNTAINING THE FILE TO BE REANMED
'''	folderprefix = RelativeFolderName(thePath)
	call CrackExt(lcase(fi.name), theFilename, theExt)
	tmp = CF(theFilename, maxNumbers)
	prefix = ""
	before = lcase(fi.name)
	after = folderprefix & "_" & prefix & lcase(tmp & theExt) 
'	msgbox " Before=<" & before & "> After=<" & after & ">" '---------------------------<<<
	On Error Resume Next
	resultname = folderprefix & "_" & prefix & lcase(tmp & theExt) 
End Sub
'-----------------------------------------------------
Function CF (old1, n)
' filename string only (no extension)
dim i, j, k, l, p1, p2, tmp1, t1, t2, r1, m1, q1, q2, dash
tmp1 = trim(old1)
l=len(tmp1)
t1 = tmp1
q1 = ""
q2 = ""
m1 = ""
t2 = ""
dash = ""
p1 = instr(tmp1, "(") 
p2 = instr(tmp1, ")")
if (p1 > 0) AND (p2 > 0) AND (p2 > p1+1) then
	q1 = "("
	q2 = ")"
	if p2 <> l then dash = "-"
	l=len(tmp1)'
	t1 = left(tmp1,p1-1)
	t2 = right(tmp1,len(tmp1)-p2)
	m1 = mid(tmp1, p1+1, p2-p1-1)
	if IsNumeric(m1) then
		m1 = Cfmt(m1,n)
'		tmp1 = t1 & m1 & t2
	end if
end if
CF = q1 & Cright(m1,n) & q2 & Cright(t1,n) & dash & Cright(t2,n)
End Function
'-----------------------------------------------------
Function Cfmt(s, n)
dim l, ss, i, j, k
ss = trim(s)
l = len(ss)
if IsNumeric(ss) then
	if (l <= n) then
		ss = string(n-l,"0") & ss 
	end if
end if
Cfmt = ss
End Function
'-----------------------------------------------------
Function Cright(s, n)
dim l, ss, i, j, k, t1, t2
ss = trim(s)
l = len(ss)
k = 0
if l > 0 then
	for i=l to 1 Step -1
		if Not IsNumeric(mid(ss, i, 1)) then
			k = i
			exit for
		end if
	next
	if k > 0 then
		t1 = left(ss,k)
		t2 = Cfmt(right(ss,l-k), n)
	else
		t1 = ""
		t2 = Cfmt(ss, n)
	end if
	ss = t1 & t2
end if
Cright = ss
End Function
'-----------------------------------------------------
Sub CrackExt(inp, f, e)
dim tmp
tmp = lcase(trim(inp))
e = trim(Mid(tmp, InStrRev(tmp, ".")))
f = trim(left(tmp, InStrRev(tmp, ".")-1))
End Sub
'-----------------------------------------------------
Function RightFolderName(inp)
dim i, j, k, l, m, n, tmp1

'ASSUME !!! a full path including a file and extension so we get rid of that bit
	tmp1 = trim(lcase(inp))
	tmp1 = trim(left(tmp1, InStrRev(tmp1, "\")-1))
	if len(tmp1) > 2 then
		tmp1 = trim(Mid(tmp1, InStrRev(tmp1, "\")+1))
	else
		tmp1 = "nil"
	end if
	RightFolderName = tmp1
End Function
'-----------------------------------------------------
Function RelativeFolderName(inp)
dim i, j, k, l, m, n, tmp1, tmp2

'ASSUME !!! a full path including a file and extension so we get rid of that bit
	tmp2 = trim(lcase(relFldr))
	tmp2 = trim(left(tmp2, InStrRev(tmp2, "\")))
	tmp1 = trim(lcase(inp))
	tmp1 = trim(left(tmp1, InStrRev(tmp1, "\")-1))
	l = len(tmp1) - len(tmp2)
	if l>0 then
		tmp1 = trim(right(tmp1,l))
	else
		tmp1 = "nil"
	end if
	tmp1 = replace(tmp1,"\","-")
	RelativeFolderName = tmp1
End Function
