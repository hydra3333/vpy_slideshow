@ECHO OFF
@setlocal ENABLEDELAYEDEXPANSION
@setlocal enableextensions

REM produces a video of a folder

set "vs_path=C:\SOFTWARE\Vapoursynth-x64"
if /I NOT "%vs_path:~-1%" == "\" (set "vs_path=%vs_path%\")

set "pwd=%CD%"
if /I NOT "%pwd:~-1%" == "\" (set "pwd=%pwd%\")

set   "script=%pwd%test_mediainfo.vpy"
REM "%vs_path%python.exe" "%script%"
"%vs_path%python.exe" "%script%" >"%script%.log" 2>&1

pause
goto :eof


REM https://www.computerhope.com/findstr.htm#:~:text=The%20findstr%20(short%20for%20find,specific%20string%20of%20plain%20text.

findstr /L /I  /c:"matrix_coefficients" .\test_mediainfo.vpy.log | sort /unique >.\z-matrix_coefficients.txt
type .\z-matrix_coefficients.txt
findstr /L /I  /c:"colour_primaries" .\test_mediainfo.vpy.log | sort /unique >.\z-colour_primaries.txt
type .\z-colour_primaries.txt
findstr /L /I  /c:"transfer_characteristics" .\test_mediainfo.vpy.log | sort /unique >.\z-transfer_characteristics.txt
type .\z-transfer_characteristics.txt
findstr /L /I  /c:"colour_range" .\test_mediainfo.vpy.log | sort /unique >.\z-colour_range.txt
type .\z-colour_range.txt
findstr /L /I  /c:"Standard" .\test_mediainfo.vpy.log | sort /unique >.\z-Standard.txt
type .\z-Standard.txt
findstr /L /I  /c:"ColorSpace" .\test_mediainfo.vpy.log | sort /unique >.\z-ColorSpace.txt
type .\z-ColorSpace.txt
findstr /L /I  /c:"ChromaSubsampling" .\test_mediainfo.vpy.log | sort /unique >.\z-ChromaSubsampling.txt
type .\z-ChromaSubsampling.txt


pause
goto :eof

# Create some translation tables from mediainfo return values to "vs" constants
# values of video stream Standard seen returned by  mediainfo
# used to inform other chouces
mi_standard_list = { 'Component', 'NTSC', 'PAL', None,}
# values of video stream colour_primaries seen returned by  mediainfo
# used to convert mediainfo to "vs" ColorPrimaries
mi_color_primaries_dict = {			'BT.2020' : 				vs.ColorPrimaries.PRIMARIES_BT2020,
									'BT.601 NTSC' :				vs.ColorPrimaries.PRIMARIES_ST170_M,		# ? newer than ColorPrimaries.PRIMARIES_BT470_M 
									'BT.601 PAL' :				vs.ColorPrimaries.PRIMARIES_BT470_BG,
									'BT.709' :					vs.ColorPrimaries.PRIMARIES_BT709,
									#None :						None,
									# not seen, check them anyway
									'BT.470_BG' :				vs.ColorPrimaries.PRIMARIES_BT470_BG,
									'BT.470 BG' :				vs.ColorPrimaries.PRIMARIES_BT470_BG,
									'BT.470 PAL :				vs.ColorPrimaries.PRIMARIES_BT470_BG,
									'BT.470_PAL :				vs.ColorPrimaries.PRIMARIES_BT470_BG,
									'BT.470_M' :				vs.ColorPrimaries.PRIMARIES_ST170_M,
									'BT.470 M' :				vs.ColorPrimaries.PRIMARIES_ST170_M,
									'BT.470 NTSC' :				vs.ColorPrimaries.PRIMARIES_ST170_M,
									}
# values of video stream transfer_characteristics seen returned by  mediainfo
# used to convert mediainfo to "vs" TransferCharacteristics
mi_transfer_characteristics_dict = {'BT.470 System B/G' :		vs.TransferCharacteristics.TRANSFER_BT470_BG,
									'BT.601' :					vs.TransferCharacteristics.TRANSFER_BT601,
									'BT.709' :					vs.TransferCharacteristics.TRANSFER_BT709 ,
									#None :						None,
									# not seen, check them anyway
									'BT.470 System M' :			vs.TransferCharacteristics.TRANSFER_BT470_M,
									'BT.BT2020 10' :			vs.TransferCharacteristics.TRANSFER_BT2020_10,
									'BT.BT2020 12' :			vs.TransferCharacteristics.TRANSFER_BT2020_12,
									'ST.2084' :					vs.TransferCharacteristics.TRANSFER_ST2084,
									}
# values of video stream matrix_coefficients seen returned by  mediainfo
# used to convert mediainfo to "vs" MatrixCoefficients
mc_bt6021 = vs.MatrixCoefficients.MATRIX_BT470_BG
if 'Standard' in mediainfo_specs:
	if 'NTSC'.lower() in mediainfo_specs['Standard'].lower():
		mc_bt601 = vs.MatrixCoefficients.MATRIX_ST170_M
if 'colour_primaries' in mediainfo_specs:
	if 'NTSC'.lower() in  mediainfo_specs['colour_primaries'].lower():	# if the substring string is inthe string
		mc_bt601 = vs.MatrixCoefficients.MATRIX_ST170_M
	if  mediainfo_specs['colour_primaries'].lower() in list(map(str.lower,[ 'BT.470 M', 'BT.470 M', 'BT.470_M', 'BT.601 NTSC', 'BT.470 NTSC' ]):
		mc_bt601 = vs.MatrixCoefficients.MATRIX_ST170_M
mi_matrix_coefficients_dict = {		'BT.470 System B/G' :		vs.MatrixCoefficients.MATRIX_BT470_BG,
									'BT.601' : 					mc_bt601,									# assume PAL unless colour_primaries/Standard say NTSC then vs.MatrixCoefficients.MATRIX_ST170_M 
									'BT.709' :					vs.MatrixCoefficients.MATRIX_BT709,
									'BT.2020 non-constant' :	vs.MatrixCoefficients.MATRIX_BT2020_NCL,
									'BT.2020 constant' :		vs.MatrixCoefficients.MATRIX_BT2020_CL,
									#None :						None,
									# not seen, check them anyway
									}
# values of video stream colour_range seen returned by  mediainfo
# used to convert mediainfo to "vs" ColorRange
mi_colour_range_dict = {			'Full'						vs.ColorRange.RANGE_FULL,
									'Limited' :					vs.ColorRange.RANGE_LIMITED,
									#None :						None,
									}





DEBUG: vs.PresetFormat ENUM: PresetFormat.NONE = 0
DEBUG: vs.PresetFormat ENUM: PresetFormat.GRAY8 = 268959744
DEBUG: vs.PresetFormat ENUM: PresetFormat.GRAY9 = 269025280
DEBUG: vs.PresetFormat ENUM: PresetFormat.GRAY10 = 269090816
DEBUG: vs.PresetFormat ENUM: PresetFormat.GRAY12 = 269221888
DEBUG: vs.PresetFormat ENUM: PresetFormat.GRAY14 = 269352960
DEBUG: vs.PresetFormat ENUM: PresetFormat.GRAY16 = 269484032
DEBUG: vs.PresetFormat ENUM: PresetFormat.GRAY32 = 270532608
DEBUG: vs.PresetFormat ENUM: PresetFormat.GRAYH = 286261248
DEBUG: vs.PresetFormat ENUM: PresetFormat.GRAYS = 287309824
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV410P8 = 805831170
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV411P8 = 805831168
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV440P8 = 805830657
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV420P8 = 805830913
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV422P8 = 805830912
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV444P8 = 805830656
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV420P9 = 805896449
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV422P9 = 805896448
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV444P9 = 805896192
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV420P10 = 805961985
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV422P10 = 805961984
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV444P10 = 805961728
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV420P12 = 806093057
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV422P12 = 806093056
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV444P12 = 806092800
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV420P14 = 806224129
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV422P14 = 806224128
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV444P14 = 806223872
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV420P16 = 806355201
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV422P16 = 806355200
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV444P16 = 806354944
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV444PH = 823132160
DEBUG: vs.PresetFormat ENUM: PresetFormat.YUV444PS = 824180736
DEBUG: vs.PresetFormat ENUM: PresetFormat.RGB24 = 537395200
DEBUG: vs.PresetFormat ENUM: PresetFormat.RGB27 = 537460736
DEBUG: vs.PresetFormat ENUM: PresetFormat.RGB30 = 537526272
DEBUG: vs.PresetFormat ENUM: PresetFormat.RGB36 = 537657344
DEBUG: vs.PresetFormat ENUM: PresetFormat.RGB42 = 537788416
DEBUG: vs.PresetFormat ENUM: PresetFormat.RGB48 = 537919488
DEBUG: vs.PresetFormat ENUM: PresetFormat.RGBH = 554696704
DEBUG: vs.PresetFormat ENUM: PresetFormat.RGBS = 555745280
DEBUG: vs.MatrixCoefficients ENUM: MatrixCoefficients.MATRIX_RGB = 0
DEBUG: vs.MatrixCoefficients ENUM: MatrixCoefficients.MATRIX_BT709 = 1
DEBUG: vs.MatrixCoefficients ENUM: MatrixCoefficients.MATRIX_UNSPECIFIED = 2
DEBUG: vs.MatrixCoefficients ENUM: MatrixCoefficients.MATRIX_FCC = 4
DEBUG: vs.MatrixCoefficients ENUM: MatrixCoefficients.MATRIX_BT470_BG = 5
DEBUG: vs.MatrixCoefficients ENUM: MatrixCoefficients.MATRIX_ST170_M = 6
DEBUG: vs.MatrixCoefficients ENUM: MatrixCoefficients.MATRIX_YCGCO = 8
DEBUG: vs.MatrixCoefficients ENUM: MatrixCoefficients.MATRIX_BT2020_NCL = 9
DEBUG: vs.MatrixCoefficients ENUM: MatrixCoefficients.MATRIX_BT2020_CL = 10
DEBUG: vs.MatrixCoefficients ENUM: MatrixCoefficients.MATRIX_CHROMATICITY_DERIVED_NCL = 12
DEBUG: vs.MatrixCoefficients ENUM: MatrixCoefficients.MATRIX_CHROMATICITY_DERIVED_CL = 13
DEBUG: vs.MatrixCoefficients ENUM: MatrixCoefficients.MATRIX_ICTCP = 14
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_BT709 = 1
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_UNSPECIFIED = 2
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_BT470_M = 4
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_BT470_BG = 5
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_BT601 = 6
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_ST240_M = 7
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_LINEAR = 8
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_LOG_100 = 9
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_LOG_316 = 10
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_IEC_61966_2_4 = 11
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_IEC_61966_2_1 = 13
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_BT2020_10 = 14
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_BT2020_12 = 15
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_ST2084 = 16
DEBUG: vs.TransferCharacteristics ENUM: TransferCharacteristics.TRANSFER_ARIB_B67 = 18
DEBUG: vs.ColorPrimaries ENUM: ColorPrimaries.PRIMARIES_BT709 = 1
DEBUG: vs.ColorPrimaries ENUM: ColorPrimaries.PRIMARIES_UNSPECIFIED = 2
DEBUG: vs.ColorPrimaries ENUM: ColorPrimaries.PRIMARIES_BT470_M = 4
DEBUG: vs.ColorPrimaries ENUM: ColorPrimaries.PRIMARIES_BT470_BG = 5
DEBUG: vs.ColorPrimaries ENUM: ColorPrimaries.PRIMARIES_ST170_M = 6
DEBUG: vs.ColorPrimaries ENUM: ColorPrimaries.PRIMARIES_ST240_M = 7
DEBUG: vs.ColorPrimaries ENUM: ColorPrimaries.PRIMARIES_FILM = 8
DEBUG: vs.ColorPrimaries ENUM: ColorPrimaries.PRIMARIES_BT2020 = 9
DEBUG: vs.ColorPrimaries ENUM: ColorPrimaries.PRIMARIES_ST428 = 10
DEBUG: vs.ColorPrimaries ENUM: ColorPrimaries.PRIMARIES_ST431_2 = 11
DEBUG: vs.ColorPrimaries ENUM: ColorPrimaries.PRIMARIES_ST432_1 = 12
DEBUG: vs.ColorPrimaries ENUM: ColorPrimaries.PRIMARIES_EBU3213_E = 22
DEBUG: vs.ColorRange ENUM: ColorRange.RANGE_FULL = 0
DEBUG: vs.ColorRange ENUM: ColorRange.RANGE_LIMITED = 1
DEBUG: vs.ColorFamily ENUM: ColorFamily.UNDEFINED = 0
DEBUG: vs.ColorFamily ENUM: ColorFamily.GRAY = 1
DEBUG: vs.ColorFamily ENUM: ColorFamily.RGB = 2
DEBUG: vs.ColorFamily ENUM: ColorFamily.YUV = 3
DEBUG: vs.ChromaLocation ENUM: ChromaLocation.CHROMA_LEFT = 0
DEBUG: vs.ChromaLocation ENUM: ChromaLocation.CHROMA_CENTER = 1
DEBUG: vs.ChromaLocation ENUM: ChromaLocation.CHROMA_TOP_LEFT = 2
DEBUG: vs.ChromaLocation ENUM: ChromaLocation.CHROMA_TOP = 3
DEBUG: vs.ChromaLocation ENUM: ChromaLocation.CHROMA_BOTTOM_LEFT = 4
DEBUG: vs.ChromaLocation ENUM: ChromaLocation.CHROMA_BOTTOM = 5
DEBUG: vs.FieldBased ENUM: FieldBased.FIELD_PROGRESSIVE = 0
DEBUG: vs.FieldBased ENUM: FieldBased.FIELD_TOP = 2
DEBUG: vs.FieldBased ENUM: FieldBased.FIELD_BOTTOM = 1