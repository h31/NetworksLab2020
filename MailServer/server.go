package MailServer

import (
	"database/sql"
	"encoding/json"
	_ "github.com/mattn/go-sqlite3"
	"io/ioutil"
	"log"
	"math/rand"
	"net/http"
	"strconv"
	"time"
)

var database *sql.DB

var sessions map[int]string

type UserSegment struct {
	Id    int    `json:"id"`
	Token string `json:"token"`
}

type LoginForm struct {
	Id    int
	Login string `json:"login"`
	Pass  string `json:"pass"`
}

type ListForm struct {
	Id     int       `json:"id"`
	From   string    `json:"from"`
	To     string    `json:"to"`
	Re     string    `json:"re"`
	Sdate  time.Time `json:"sdate"`
	Status int       `json:"status"`
}

type MessageForm struct {
	Id     int       `json:"id"`
	From   string    `json:"from"`
	To     string    `json:"to"`
	Re     string    `json:"re"`
	Body   string    `json:"body"`
	Sdate  time.Time `json:"sdate"`
	Status int       `json:"status"`
}

var letterRunes = []rune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

func RandStringRunes(n int) string {
	b := make([]rune, n)
	for i := range b {
		b[i] = letterRunes[rand.Intn(len(letterRunes))]
	}
	return string(b)
}

func LoginAction(w http.ResponseWriter, r *http.Request) {
	b, err := ioutil.ReadAll(r.Body)
	if err != nil {
		http.Error(w, err.Error(), 500)
	}
	var form LoginForm
	err = json.Unmarshal(b, &form)
	if err != nil {
		http.Error(w, err.Error(), 500)
	}
	row := database.QueryRow("select * from users where login = $1 and pass = $2", form.Login, form.Pass)
	err = row.Scan(&form.Id, &form.Login, &form.Pass)
	if err != nil {
		log.Println(err)
		w.Write([]byte("null"))
	} else {
		rand.Seed(time.Now().UnixNano())
		answer := RandStringRunes(32)
		sessions[form.Id] = answer
		resp, err := json.Marshal(UserSegment{
			Id:    form.Id,
			Token: answer,
		})
		if err != nil {
			http.Error(w, http.StatusText(405), 405)
		} else {
			w.Write(resp)
		}
	}
}

func ListAction(w http.ResponseWriter, r *http.Request) {
	b, err := ioutil.ReadAll(r.Body)
	if err != nil {
		http.Error(w, err.Error(), 500)
	}
	var user UserSegment
	err = json.Unmarshal(b, &user)
	if tok, ok := sessions[user.Id]; err != nil || !ok || tok != user.Token {
		http.Error(w, err.Error(), 500)
	}
	rows, err := database.Query("select inb.id, u.login, u2.login, inb.re, inb.status, inb.sdate from inboxes inb inner join users u on u.id = inb.\"from\" inner join users u2 on u2.id = inb.\"to\" where inb.\"to\" = $1", user.Id)
	defer rows.Close()
	if err != nil {
		http.Error(w, err.Error(), 500)
	} else {
		var messages []ListForm
		for rows.Next() {
			msg := ListForm{}
			err := rows.Scan(&msg.Id, &msg.From, &msg.To, &msg.Re, &msg.Status, &msg.Sdate)
			if err != nil {
				http.Error(w, err.Error(), 500)
				break
			}
			messages = append(messages, msg)
		}
		ans, err := json.Marshal(messages)
		if err != nil {
			http.Error(w, err.Error(), 500)

		} else {
			w.Write(ans)
		}
	}
}

func MessageAction(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case "GET":
		b, err := ioutil.ReadAll(r.Body)
		if err != nil {
			http.Error(w, err.Error(), 500)
		}
		var user UserSegment
		err = json.Unmarshal(b, &user)
		if tok, ok := sessions[user.Id]; err != nil || !ok || tok != user.Token {
			http.Error(w, err.Error(), 500)
		} else {
			id, _ := strconv.Atoi(r.URL.Query().Get("id"))
			row := database.QueryRow("select inb.id, u.login, u2.login, inb.re, inb.body, inb.status, inb.sdate from inboxes inb inner join users u on u.id = inb.\"from\" inner join users u2 on u2.id = inb.\"to\" where (inb.\"to\" = $1 or inb.\"from\" = $2) and inb.id = $3", user.Id, user.Id, id)
			msg := MessageForm{}
			err = row.Scan(&msg.Id, &msg.From, &msg.To, &msg.Re, &msg.Body, &msg.Status, &msg.Sdate)
			if err != sql.ErrNoRows && err != nil {
				http.Error(w, err.Error(), 500)
			} else if err == sql.ErrNoRows {
				w.Write([]byte("null"))
			} else {
				ans, _ := json.Marshal(msg)
				w.Write(ans)
			}
		}
	case "DELETE":
		b, err := ioutil.ReadAll(r.Body)
		if err != nil {
			http.Error(w, err.Error(), 500)
		}
		var user UserSegment
		err = json.Unmarshal(b, &user)
		if tok, ok := sessions[user.Id]; err != nil || !ok || tok != user.Token {
			http.Error(w, err.Error(), 500)
		} else {
			id, _ := strconv.Atoi(r.URL.Query().Get("id"))
			row := database.QueryRow("select inb.id, u.login, u2.login, inb.re, inb.body, inb.status, inb.sdate from inboxes inb inner join users u on u.id = inb.\"from\" inner join users u2 on u2.id = inb.\"to\" where (inb.\"to\" = $1 or inb.\"from\" = $2) and inb.id = $3", user.Id, user.Id, id)
			msg := MessageForm{}
			err = row.Scan(&msg.Id, &msg.From, &msg.To, &msg.Re, &msg.Body, &msg.Status, &msg.Sdate)
			if err != nil {
				http.Error(w, err.Error(), 500)
			}
			ans, _ := json.Marshal(msg)
			_, _ = database.Exec("delete from inboxes where id = $1", id)
			w.Write(ans)
		}
	case "PUT":
		b, err := ioutil.ReadAll(r.Body)
		if err != nil {
			http.Error(w, err.Error(), 500)
		}
		var user UserSegment
		err = json.Unmarshal(b, &user)
		if tok, ok := sessions[user.Id]; err != nil || !ok || tok != user.Token {
			http.Error(w, err.Error(), 500)
		} else {
			var msg MessageForm
			err = json.Unmarshal(b, &msg)
			from := user.Id
			to, _ := strconv.Atoi(msg.To)
			res, err := database.Exec("insert into inboxes(\"from\", \"to\", re, body) values ($1, $2, $3, $4)", from, to, msg.Re, msg.Body)
			if err != nil {
				http.Error(w, err.Error(), 500)
			}
			id, _ := res.LastInsertId()
			afterId := strconv.Itoa(int(id))
			w.Write([]byte(afterId))
		}
	}
}

func LogoutAction(w http.ResponseWriter, r *http.Request) {
	b, err := ioutil.ReadAll(r.Body)
	if err != nil {
		http.Error(w, err.Error(), 500)
	}
	var user UserSegment
	err = json.Unmarshal(b, &user)
	if tok, ok := sessions[user.Id]; err != nil || !ok || tok != user.Token {
		http.Error(w, err.Error(), 500)
	}
	delete(sessions, user.Id)
	w.Write([]byte("true"))
}

func main() {
	var err error
	database, err = sql.Open("sqlite3", "flash.db")
	if err != nil {
		log.Fatalf("Cannot open database. %+v", err)
		panic(err)
	}
	sessions = make(map[int]string)
	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("Hello"))
	})
	mux.HandleFunc("/login", LoginAction)
	mux.HandleFunc("/list", ListAction)
	mux.HandleFunc("/message", MessageAction)
	mux.HandleFunc("/logout", LogoutAction)
	_ = http.ListenAndServe(":8080", mux)
}
