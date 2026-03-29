FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
USER app
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src
COPY ["ProfileService/ProfileService.csproj", "ProfileService/"]
COPY ["CommonService/CommonService.csproj", "CommonService/"]
RUN dotnet restore "./ProfileService/ProfileService.csproj"
COPY . .
WORKDIR "/src/ProfileService"
RUN dotnet build "./ProfileService.csproj" -c $BUILD_CONFIGURATION -o /app/build

FROM build AS publish
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish "./ProfileService.csproj" -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "ProfileService.dll"]
