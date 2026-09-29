from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db_connection, init_db

app = Flask(__name__)
app.config["SECRET_KEY"] = "chave-apenas-para-mensagens-da-aula"


@app.route("/")
def index():
    # Esta é uma rota Flask. Ela responde quando alguém acessa a página inicial.
    return render_template("index.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    # GET normalmente é utilizado para carregar a página.
    # POST normalmente é utilizado quando enviamos um formulário.
    if request.method == "POST":
        # Aqui buscamos os dados enviados pelo formulário.
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("Preencha todos os campos.", "danger")
            return render_template("cadastro.html")

        connection = get_db_connection()
        try:
            # Aqui executamos um INSERT no banco SQLite.
            connection.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            connection.commit()
        except Exception as error:
            # SQLite informa erro se o e-mail, que é único, já existir.
            if "UNIQUE constraint failed" in str(error):
                flash("Este e-mail já está cadastrado.", "danger")
            else:
                flash("Não foi possível concluir o cadastro.", "danger")
            return render_template("cadastro.html")
        finally:
            connection.close()

        flash("Conta criada! Agora faça seu acesso.", "success")
        # redirect envia o usuário para outra rota.
        return redirect(url_for("login"))

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = get_db_connection()
        # Aqui buscamos um usuário pelo e-mail usando SELECT.
        user = connection.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        connection.close()

        if user and check_password_hash(user["password"], password):
            # Em um sistema real, use sessões e autenticação adequada.
            # Neste exemplo, o objetivo é apenas praticar formulário e validação.
            return redirect(url_for("sistema"))

        flash("E-mail ou senha incorretos.", "danger")

    return render_template("login.html")


@app.route("/sistema")
def sistema():
    return render_template("sistema.html")


# EXEMPLO:
# Cada grupo deverá substituir "records" pela entidade principal
# do seu próprio projeto, como livros, pacientes ou produtos.
@app.route("/sistema/registros")
def listar_registros():
    connection = get_db_connection()
    records = connection.execute(
        "SELECT * FROM records ORDER BY created_at DESC"
    ).fetchall()
    connection.close()
    return render_template("registros.html", records=records)

@app.route("/sistema/doadores")
def listar_doadores():
    connection = get_db_connection()
    records = connection.execute(
        "SELECT * FROM doadores ORDER BY created_at DESC"
    ).fetchall()
    connection.close()
    return render_template("doadores.html", records=records)



@app.route("/sistema/doadores/novo", methods=["GET", "POST"])
def novo_doador():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        blood_type = request.form["blood_type"].strip()

        if not name:
            flash("Informe o nome do doador.", "danger")
            return render_template("doador_form.html", record=None)

        connection = get_db_connection()
        existing_donor = connection.execute(
            "SELECT id FROM doadores WHERE email = ?", (email,)
        ).fetchone()
        if existing_donor:
            connection.close()
            flash("Já existe um doador cadastrado com este e-mail.", "danger")
            return render_template("doador_form.html", record=None)

        connection.execute(
            "INSERT INTO doadores (name, email, blood_type) VALUES (?, ?, ?)",
            (name, email, blood_type),
        )
        connection.commit()
        connection.close()
        flash("Doador cadastrado com sucesso.", "success")
        return redirect(url_for("listar_doadores"))

    return render_template("doador_form.html", record=None)


@app.route("/sistema/registros/novo", methods=["GET", "POST"])
def novo_registro():
    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()

        if not title:
            flash("Informe um título para o registro.", "danger")
            return render_template("registro_form.html", record=None)

        connection = get_db_connection()
        connection.execute(
            "INSERT INTO records (title, description) VALUES (?, ?)",
            (title, description),
        )
        connection.commit()
        connection.close()
        flash("Registro criado com sucesso.", "success")
        return redirect(url_for("listar_registros"))

    return render_template("registro_form.html", record=None)


@app.route("/sistema/registros/<int:record_id>/editar", methods=["GET", "POST"])
def editar_registro(record_id):
    connection = get_db_connection()
    record = connection.execute(
        "SELECT * FROM records WHERE id = ?", (record_id,)
    ).fetchone()

    if record is None:
        connection.close()
        flash("Registro não encontrado.", "danger")
        return redirect(url_for("listar_registros"))

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        if not title:
            connection.close()
            flash("Informe um título para o registro.", "danger")
            return render_template("registro_form.html", record=record)

        # UPDATE altera dados que já existem no banco.
        connection.execute(
            "UPDATE records SET title = ?, description = ? WHERE id = ?",
            (title, description, record_id),
        )
        connection.commit()
        connection.close()
        flash("Registro atualizado com sucesso.", "success")
        return redirect(url_for("listar_registros"))

    connection.close()
    return render_template("registro_form.html", record=record)


@app.route("/sistema/doadores/<int:record_id>/editar", methods=["GET", "POST"])
def editar_doador(record_id):
    connection = get_db_connection()
    record = connection.execute(
        "SELECT * FROM doadores WHERE id = ?", (record_id,)
    ).fetchone()

    if record is None:
        connection.close()
        flash("Registro não encontrado.", "danger")
        return redirect(url_for("listar_doadores"))

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        blood_type = request.form["blood_type"].strip()
        if not name:
            connection.close()
            flash("Informe um nome para o doador.", "danger")
            return render_template("doador_form.html", record=record)

        existing_donor = connection.execute(
            "SELECT id FROM doadores WHERE email = ? AND id != ?",
            (email, record_id),
        ).fetchone()
        if existing_donor:
            connection.close()
            flash("Já existe um doador cadastrado com este e-mail.", "danger")
            return render_template("doador_form.html", record=record)

        # UPDATE altera dados que já existem no banco.
        connection.execute(
            "UPDATE doadores SET name = ?, email = ?, blood_type = ? WHERE id = ?",
            (name, email, blood_type, record_id),
        )
        connection.commit()
        connection.close()
        flash("Registro atualizado com sucesso.", "success")
        return redirect(url_for("listar_doadores"))

    connection.close()
    return render_template("doador_form.html", record=record)


@app.route("/sistema/registros/<int:record_id>/excluir", methods=["POST"])
def excluir_registro(record_id):
    connection = get_db_connection()
    # DELETE remove um registro. Por isso, usamos POST para esta ação.
    connection.execute("DELETE FROM records WHERE id = ?", (record_id,))
    connection.commit()
    connection.close()
    flash("Registro excluído.", "success")
    return redirect(url_for("listar_registros"))


@app.route("/sistema/doadores/<int:record_id>/excluir", methods=["POST"])
def excluir_doador(record_id):
    connection = get_db_connection()
    connection.execute("DELETE FROM doadores WHERE id = ?", (record_id,))
    connection.commit()
    connection.close()
    flash("Doador excluído.", "success")
    return redirect(url_for("listar_doadores"))


if __name__ == "__main__":
    # Cria as tabelas na primeira execução, caso ainda não existam.
    init_db()
    app.run(debug=True)
