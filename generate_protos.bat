@echo off
set GRPC_PYTHON_BIN="python -m grpc_tools.protoc"
set OUTPUT_DIR=./generated

echo Checking if %OUTPUT_DIR% exists...
if not exist %OUTPUT_DIR% (
    echo Creating %OUTPUT_DIR% directory...
    mkdir %OUTPUT_DIR%
)

echo Starting Protobuf compilation...
:: The -I. tells protoc where to find the source .proto files (in the current directory)
:: --python_out and --grpc_python_out tell it where to place the output files.
%GRPC_PYTHON_BIN% -I. --python_out=%OUTPUT_DIR% --grpc_python_out=%OUTPUT_DIR% *.proto

if errorlevel 1 (
    echo.
    echo ERROR: Protobuf compilation failed! Ensure "grpcio" and "grpcio-tools" are installed.
) else (
    echo.
    echo Successfully generated Python gRPC stubs in %OUTPUT_DIR%.
)

pause