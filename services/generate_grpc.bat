@echo off
echo Generating gRPC code from proto files...

REM Create directories if they don't exist
if not exist "generated" mkdir generated

REM Generate for auth service
python -m grpc_tools.protoc -I./protos --python_out=./generated --grpc_python_out=./generated ./protos/auth.proto

REM Generate for course service
python -m grpc_tools.protoc -I./protos --python_out=./generated --grpc_python_out=./generated ./protos/course.proto

REM Generate for enrollment service
python -m grpc_tools.protoc -I./protos --python_out=./generated --grpc_python_out=./generated ./protos/enrollment.proto

echo Done! Generated files are in .\generated\
pause