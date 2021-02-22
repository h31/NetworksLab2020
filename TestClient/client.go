package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
)

var id int
var token string

func main() {
	var input string

	reader := bufio.NewReader(os.Stdin)
	print("Hello. You have registration on test system? [y/n]> ")
	for input, _ = reader.ReadString('\n'); input != "y\n" && input != "n\n"; input, _ = reader.ReadString('\n') {
	}
	if input == "y\n" {
		form := map[string]interface{}{
			"login": "",
			"pass":  "",
		}
		print("Login> ")
		for input, _ = reader.ReadString('\n'); input == "\n"; input, _ = reader.ReadString('\n') {
		}
		form["login"] = strings.TrimSpace(input)
		print("Password> ")
		for input, _ = reader.ReadString('\n'); input == "\n"; input, _ = reader.ReadString('\n') {
		}
		form["pass"] = strings.TrimSpace(input)
		jsBytes, err := json.Marshal(form)
		if err != nil {
			log.Fatalln(err)
		}
		r, err := http.NewRequest(http.MethodPost, "http://localhost:5000/login", bytes.NewReader(jsBytes))
		if err != nil {
			log.Fatalln(err)
			return
		}
		client := http.Client{}
		resp, _ := client.Do(r)
		if resp.StatusCode == 401 {
			println("Invalid user login/pass")
			return
		}
		var result map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&result)
		id = int(result["id"].(float64))
		token = result["token"].(string)
		resp.Body.Close()
		println("Authentication successes")
	} else {
		form := map[string]interface{}{
			"login": "",
			"pass":  "",
			"name":  "",
		}
		print("Login> ")
		for input, _ = reader.ReadString('\n'); input == "\n"; input, _ = reader.ReadString('\n') {
		}
		form["login"] = strings.TrimSpace(input)
		print("Password> ")
		for input, _ = reader.ReadString('\n'); input == "\n"; input, _ = reader.ReadString('\n') {
		}
		form["pass"] = strings.TrimSpace(input)
		print("User`s name> ")
		for input, _ = reader.ReadString('\n'); input == "\n"; input, _ = reader.ReadString('\n') {
		}
		form["name"] = strings.TrimSpace(input)
		jsBytes, err := json.Marshal(form)
		if err != nil {
			log.Fatalln(err)
		}
		r, err := http.NewRequest(http.MethodPost, "http://localhost:5000/register", bytes.NewReader(jsBytes))
		if err != nil {
			log.Fatalln(err)
			return
		}
		resp, _ := (&http.Client{}).Do(r)
		if resp.StatusCode == 401 {
			println("Invalid user login/pass")
			return
		}
		var result map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&result)
		id = result["id"].(int)
		token = result["token"].(string)
		resp.Body.Close()
		println("Registration successes")
	}
	print("Command> ")
	for input, _ = reader.ReadString('\n'); true; input, _ = reader.ReadString('\n') {
		client := http.Client{}
		switch strings.TrimSpace(input) {
		case "quit":
			form := map[string]interface{}{
				"id":    id,
				"token": token,
			}
			jsBytes, err := json.Marshal(form)
			if err != nil {
				log.Fatalln(err)
			}
			r, _ := http.NewRequest(http.MethodGet, "http://localhost:5000/logout", bytes.NewReader(jsBytes))
			resp, _ := client.Do(r)
			if resp.StatusCode == 401 {
				println("the authorization token has expired. Please relogin")
				return
			}
			res, _ := ioutil.ReadAll(resp.Body)
			if string(res) != "ok" {
				println("Error of logout")
			} else {
				println("Logout completed. Bye-bye")
			}
			break
		case "list":
			form := map[string]interface{}{
				"id":    id,
				"token": token,
			}
			jsBytes, err := json.Marshal(form)
			if err != nil {
				log.Fatalln(err)
			}
			r, _ := http.NewRequest(http.MethodGet, "http://localhost:5000/list", bytes.NewReader(jsBytes))
			resp, _ := client.Do(r)
			if resp.StatusCode == 401 {
				println("the authorization token has expired. Please relogin")
				return
			}
			var result []interface{}
			err = json.NewDecoder(resp.Body).Decode(&result)
			fmt.Printf("%-4s | %-64s |\n", "Id", "Name")
			for _, row := range result {
				el := row.(map[string]interface{})
				fmt.Printf("%4d | %64s |\n", int(el["id"].(float64)), el["name"].(string))
			}
			resp.Body.Close()
		case "res":
			form := map[string]interface{}{
				"id":    id,
				"token": token,
			}
			jsBytes, err := json.Marshal(form)
			if err != nil {
				log.Fatalln(err)
			}
			r, _ := http.NewRequest(http.MethodGet, "http://localhost:5000/res", bytes.NewReader(jsBytes))
			resp, _ := client.Do(r)
			if resp.StatusCode == 401 {
				println("the authorization token has expired. Please relogin")
				return
			}
			var result map[string]string
			err = json.NewDecoder(resp.Body).Decode(&result)
			fmt.Printf("Your last test was \"%s\". Mark %s\n", result["name"], result["result"])
		case "start":
			print("Id of test> ")
			input, _ := reader.ReadString('\n')
			input = strings.TrimSpace(input)
			form := map[string]interface{}{
				"id":    id,
				"token": token,
				"test":  strconv.Atoi(input),
			}
			jsBytes, err := json.Marshal(form)
			if err != nil {
				log.Fatalln(err)
			}
			r, _ := http.NewRequest(http.MethodPost, "http://localhost:5000/list", bytes.NewReader(jsBytes))
			resp, _ := client.Do(r)
			if resp.StatusCode == 401 {
				println("the authorization token has expired. Please relogin")
				return
			}
			var result map[string]interface{}
			err = json.NewDecoder(resp.Body).Decode(&result)
			sid := int(result["id"].(float64))
			size := int(result["size"].(float64))
			for i := 0; i < size; i++ {
				form = map[string]interface{}{
					"id":    id,
					"token": token,
					"test":  sid,
				}
				r, _ := http.NewRequest(http.MethodGet, "http://localhost:5000/step", bytes.NewReader(jsBytes))
				resp, _ := client.Do(r)
				if resp.StatusCode == 401 {
					println("the authorization token has expired. Please relogin")
					return
				}
				var step map[string]interface{}
				err = json.NewDecoder(resp.Body).Decode(&step)
				fmt.Printf("Step %d\n", int(step["step"].(float64)))
				fmt.Printf("Question - %s\n", step["question"].(string))
				for i, s := range step["answers"].([]string) {
					fmt.Printf("%d. %s\n", i, s)
				}
				resp.Body.Close()
				print("Answer> ")
				input, _ := reader.ReadString('\n')
				input = strings.TrimSpace(input)
				form["answer"] = input
				r, _ = http.NewRequest(http.MethodGet, "http://localhost:5000/step", bytes.NewReader(jsBytes))
				resp, _ = client.Do(r)
				if resp.StatusCode != 200 {
					println("Error in testing system. Please, come back later")
					return
				}
			}
		case "help":
			println("List of command")
			println("list - get list of tests")
			println("res - get result of last test")
			println("start - start new test")
			println("help - get this page")
			println("quit")
		default:
			println("Wrong command")
			println("List of command")
			println("list - get list of tests")
			println("res - get result of last test")
			println("start - start new test")
			println("help - get this page")
			println("quit")
		}
		print("Command> ")
	}
}
