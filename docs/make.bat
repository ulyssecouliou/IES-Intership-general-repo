@echo off
set SPHINXBUILD=sphinx-build
set SOURCEDIR=source
set BUILDDIR=build
if "%LANGUAGE%" == "" set LANGUAGE=en

if "%1" == "html" (
  %SPHINXBUILD% -b html %SOURCEDIR% %BUILDDIR%\html\%LANGUAGE% -D language=%LANGUAGE%
  goto end
)

if "%1" == "gettext" (
  %SPHINXBUILD% -b gettext %SOURCEDIR% %BUILDDIR%\gettext
  goto end
)

if "%1" == "clean" (
  if exist %BUILDDIR% rmdir /s /q %BUILDDIR%
  goto end
)

%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% -D language=%LANGUAGE%

:end
