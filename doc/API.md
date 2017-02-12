## Get the Environment information

Returns the environment information based on the application version. 
Please note, the environment service location, along with game name and version should be hardcoded inside the game.

#### ← Request

```rest
GET /<game-name>/<game-version>
```

| Argument         | Description                        |
|------------------|------------------------------------|
| `<game-name>`    | Name of the current application    |
| `<game-version>` | Current version of the application |

#### → Response

In case of success, a JSON object with environment information returned:
```json
{
    "discovery": "https://dicovery-test.example.com",
    "<custom attribute>": "<custom attribute value defined for the environment>"
}
```

| Response         | Description                                          |
|------------------|------------------------------------------------------|
| `200 OK`         | Everything went OK, environment information follows. |
| `404 Not Found`  | No such Application and/or Version found             |
