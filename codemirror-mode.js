(function(mod) {
  if (typeof exports == "object" && typeof module == "object")
    mod(require("https://codemirror.net/lib/codemirror"));
  else if (typeof define == "function" && define.amd)
    define(["https://codemirror.net/lib/codemirror"], mod);
  else
    mod(CodeMirror);
})(function(CodeMirror) {
  "use strict";

  var modulesData = (function() {
    var req = new XMLHttpRequest();
    req.overrideMimeType("application/json");
    req.open('GET', 'modules.json', false);
    req.send(null);
    if (req.readyState == 4 && req.status == "200") {
      return JSON.parse(req.responseText);
    }
  })();

  for (var mod in modulesData) {
    if (modulesData[mod].params) {
      for (var param in modulesData[mod].params) {
        modulesData[mod].params[param] = RegExp().compile("^" + modulesData[mod].params[param] + "$");
      }
    }
  }

  CodeMirror.defineMode("patchbook", function() {
    return {
      startState: function() {
        return {
          nextTokens: [],
          currentModule: null,
          currentParam: null,
          singleLineParams: false,
          multiLineParams: false,
        };
      },
      token: function(stream, state) {
        if (state.nextTokens.length > 0) {
          var nextToken = state.nextTokens.shift();
          stream.eatWhile((function(n) { return function(c) { return n-- > 0; }})(nextToken.string.length));
          if ("state" in nextToken) {
            for (var k in nextToken.state) {
              state[k] = nextToken.state[k];
            }
          }
          return nextToken.type;
        }
        state.currentParam = null;
        if (stream.peek() == "/") {
          stream.next();
          if (stream.eat("/")) {
            stream.skipToEnd();
            state.singleLineParams = false;
            return "comment";
          }
        } else if (stream.sol()) {
          state.singleLineParams = false;
          stream.eatSpace();
          if (stream.eol()) {
            return null;
          }
          var ch = stream.next();
          if (state.multiLineParams && ch == "|") {
            stream.eatSpace();
            var m = stream.match(/([^=|]+?)(( *= *)([^ |\/=][^|\/=]*?)?)? *(\/|$)/, false);
            if (m) {
              var param;
              var paramConstraint;
              if (state.currentModule in modulesData
                  && modulesData[state.currentModule].params
                  && m[1] in modulesData[state.currentModule].params) {
                param = m[1];
                paramConstraint = modulesData[state.currentModule].params[param];
              } else {
                param = paramConstraint = null;
              }
              state.nextTokens.push({
                string: m[1],
                type: "param" + (paramConstraint === undefined ? " error line-error" : m[2] ? "" : " line-error"),
                state: {currentParam: param}});
              if (m[4]) {
                var invalidParam = paramConstraint && !paramConstraint.test(m[4]);
                state.nextTokens.push({string: m[3], type: null});
                state.nextTokens.push({string: m[4], type: "value" + (invalidParam ? " error line-error" : "")});
              } else if (m[3]) {
                state.nextTokens.push({string: m[3], type: "error line-error expect-value"});
              }
              return null;
            } else {
              var cur = stream.current();
              var i = cur.indexOf("|");
              if (i > 0) {
                stream.backUp(cur.length - i);
                state.nextTokens.push({string: cur.substring(i), type: "expect-param line-error"});
                return null;
              } else {
                return "expect-param line-error";
              }
            }
          } else {
            state.multiLineParams = false;
            state.currentModule = null;
            if (ch == "-") {
              stream.eatSpace();
              var m = stream.match(
                /([^:()]+?)(( *)(\( *)([^ ()][^()]*?)?( *\))?(( +[>ctpg-])(> +)(([^:()]+?)(( *)(\( *)([^ ()][^()]*?)?( *\))?)?)?)?)?( *(\/|$))/,
                false);
              if (m) {
                var module1 = m[1].toUpperCase().replace(/ .+$/, "");
                if (!module1 in modulesData) {
                  module1 = m[1];
                }
                state.nextTokens.push({
                  string: m[1],
                  type: module1 in modulesData ? "module" : "unknown module",
                  state: {currentModule: module1}});
                if (m[2]) {
                  if (m[3])
                    state.nextTokens.push({string: m[3], type: null});
                  if (m[5]) {
                    var port1 = m[5] ? m[5].replace(/[^A-Za-z0-9]/, "") : null;
                    var port1Invalid = port1 && module1 in modulesData && !modulesData[module1].ports.includes(port1);
                    state.nextTokens.push({string: m[4], type: m[6] ? null : "error line-error"});
                    state.nextTokens.push({string: m[5], type: "port" + (port1Invalid ? " error line-error" : "")});
                    if (m[6])
                      state.nextTokens.push({string: m[6], type: null});
                  } else {
                    state.nextTokens.push({string: m[4], type: "expect-port error line-error"});
                    if (m[6])
                      state.nextTokens.push({string: m[6], type: "error line-error"});
                  }
                  if (m[7]) {
                    if (m[10]) {
                      state.nextTokens.push({string: m[8] + m[9], type: "connection"});
                      var module2 = m[11].toUpperCase().replace(/ .+$/, "");
                      if (!module2 in modulesData) {
                        module2 = m[11];
                      }
                      state.nextTokens.push({
                        string: m[11],
                        type: module2 in modulesData ? "module" : "unknown module",
                        state: {currentModule: module2}});
                      if (m[12]) {
                        if (m[13])
                          state.nextTokens.push({string: m[13], type: null});
                        if (m[15]) {
                          var port2 = m[15] ? m[15].replace(/[^A-Za-z0-9]/, "") : null;
                          var port2Invalid = port2 && module2 in modulesData && !modulesData[module2].ports.includes(port2);
                          state.nextTokens.push({string: m[14], type: m[16] ? null : "error line-error"});
                          state.nextTokens.push({string: m[15], type: "port" + (port2Invalid ? " error line-error" : "")});
                          if (m[16])
                            state.nextTokens.push({string: m[16], type: null});
                        } else {
                          state.nextTokens.push({string: m[14], type: "expect-port error line-error"});
                          if (m[16])
                            state.nextTokens.push({string: m[16], type: "error line-error"});
                        }
                        return null;
                      }
                    } else {
                      state.nextTokens.push({string: m[8], type: "connection"});
                      state.nextTokens.push({string: m[9], type: "connection expect-module"});
                      return "line-error";
                    }
                  }
                }
                return "line-error";
              } else {
                var cur = stream.current();
                var i = cur.indexOf("-");
                if (i > 0) {
                  stream.backUp(cur.length - i);
                  state.nextTokens.push({string: cur.substring(i), type: "expect-module line-error"});
                  return null;
                } else {
                  return "expect-module line-error";
                }
              }
            } else if (ch == "*") {
              stream.eatSpace();
              var m = stream.match(/([^:()]+?)( *)((: *)([^\/])?|\/|$)/, false);
              if (m) {
                state.currentModule = m[1].toUpperCase().replace(/ .+$/, "");
                if (!state.currentModule in modulesData) {
                  state.currentModule = m[1];
                }
                state.nextTokens.push({string: m[1], type: state.currentModule in modulesData ? "module" : "unknown module"});
                if (m[2])
                  state.nextTokens.push({string: m[2], type: null});
                if (m[4]) {
                  state.nextTokens.push({
                    string: m[4],
                    type: (m[5] || !m[4].endsWith(" ") || /^ *\|/.test(stream.lookAhead(1))) ? null : "expect-param"});
                  state.singleLineParams = m[5];
                  state.multiLineParams = !state.singleLineParams;
                  return null;
                }
                return "line-error";
              } else {
                var cur = stream.current();
                var i = cur.indexOf("*");
                if (i > 0) {
                  stream.backUp(cur.length - i);
                  state.nextTokens.push({string: cur.substring(i), type: "expect-module line-error"});
                  return null;
                } else {
                  return "expect-module line-error";
                }
              }
            }
          }
        } else if (state.singleLineParams) {
          stream.eatSpace();
          var m = stream.match(/([^=|]+?)(( *= *)([^ |\/=][^|\/=]*?)?)?( *)($|\/|((\| *)([^ \/])?))/, false);
          if (m) {
            var param;
            var paramConstraint;
            if (state.currentModule in modulesData
                && modulesData[state.currentModule].params
                && m[1] in modulesData[state.currentModule].params) {
              param = m[1];
              paramConstraint = modulesData[state.currentModule].params[param];
            } else {
              param = paramConstraint = null;
            }
            state.nextTokens.push({
              string: m[1],
              type: "param" + (paramConstraint === undefined ? " error line-error" : m[2] ? "" : " line-error"),
              state: {currentParam: param}});
            if (m[4]) {
              var invalidParam = paramConstraint && !paramConstraint.test(m[4]);
              state.nextTokens.push({string: m[3], type: null});
              state.nextTokens.push({string: m[4], type: "value" + (invalidParam ? " error line-error" : "")});
            } else if (m[3]) {
              state.nextTokens.push({string: m[3], type: "error line-error expect-value"});
            }
            if (m[7]) {
              state.nextTokens.push({string: m[5], type: null});
              state.nextTokens.push({string: m[8], type: m[9] ? null : "error error-line expect-param"});
            } else {
              state.singleLineParams = false;
            }
            return null;
          }
        }
        if (stream.eatSpace()) {
          return null;
        } else {
          stream.skipToEnd();
          state.singleLineParams = false;
          return "error line-error";
        }
      }
    };
  });

  CodeMirror.registerHelper("hint", "patchbook", function(editor, options) {
    var cursor = editor.getCursor();
    var token = editor.getTokenAt(cursor);
    if (token.type) {
      var types = token.type.split(/ +/);
      if (token.state.currentModule
          && (types.includes("port") || types.includes("expect-port"))
          && token.state.currentModule in modulesData) {
        var candidates = modulesData[token.state.currentModule].ports;
        var word = types.includes("port") ? token.string : "";
        var start = types.includes("port") ? token.start : cursor.ch;
        var end = types.includes("port") ? token.end : cursor.ch;
        candidates = candidates.filter(x => x.startsWith(word));
        if (candidates.length > 0 && !(candidates.length == 1 && candidates[0] == word)) {
          var r = {
            list: candidates,
            from: CodeMirror.Pos(cursor.line, start),
            to: CodeMirror.Pos(cursor.line, end)
          };
          if (!editor.getLine(cursor.line).substring(end).match(/^ *\)/)) {
            CodeMirror.on(r, "pick", function(picked) {
              editor.getDoc().replaceRange(")", {line: cursor.line, ch: start + picked.length});
            });
          }
          return r;
        }
      } else if (token.state.currentModule
                 && (types.includes("param") || types.includes("expect-param"))
                 && token.state.currentModule in modulesData) {
        var candidates = Object.keys(modulesData[token.state.currentModule].params || {});
        var word = types.includes("param") ? token.string : "";
        var start = types.includes("param") ? token.start : cursor.ch;
        var end = types.includes("param") ? token.end : cursor.ch;
        candidates = candidates.filter(x => x.startsWith(word));
        if (candidates.length > 0 && !(candidates.length == 1 && candidates[0] == word)) {
          var r = {
            list: candidates,
            from: CodeMirror.Pos(cursor.line, start),
            to: CodeMirror.Pos(cursor.line, end)
          };
          if (!editor.getLine(cursor.line).substring(end).match(/^ *=/)) {
            CodeMirror.on(r, "pick", function(picked) {
              editor.getDoc().replaceRange(" = ", {line: cursor.line, ch: start + picked.length});
              CodeMirror.commands.autocomplete(editor, null, {completeSingle: false});
            });
          }
          return r;
        }
      } else if (types.includes("module") || types.includes("expect-module")) {
        var candidates = Object.keys(modulesData);
        var word = types.includes("module") ? token.string : "";
        var start = types.includes("module") ? token.start : cursor.ch;
        var end = types.includes("module") ? token.end : cursor.ch;
        word = word.toUpperCase();
        candidates = candidates.filter(x => x.startsWith(word));
        if (candidates.length > 0 && !(candidates.length == 1 && candidates[0] == word)) {
          var r = {
            list: candidates,
            from: CodeMirror.Pos(cursor.line, start),
            to: CodeMirror.Pos(cursor.line, end)
          }
          var line = editor.getLine(cursor.line);
          if (line.match(/^ *-/) && !line.substring(end).match(/^ *\(/)) {
            CodeMirror.on(r, "pick", function(picked) {
              editor.getDoc().replaceRange(" (", {line: cursor.line, ch: start + picked.length});
              CodeMirror.commands.autocomplete(editor, null, {completeSingle: false});
            });
          } else if (line.match(/^ *\*/) && !line.substring(end).match(/^ *:/)) {
            CodeMirror.on(r, "pick", function(picked) {
              editor.getDoc().replaceRange(":", {line: cursor.line, ch: start + picked.length});
            });
          }
          return r;
        }
      } else if (token.state.currentParam
                 && (types.includes("value") || types.includes("expect-value"))) {
        var candidates = regexToPossibleValues(modulesData[token.state.currentModule].params[token.state.currentParam]);
        var word = types.includes("value") ? token.string : "";
        var start = types.includes("value") ? token.start : cursor.ch;
        var end = types.includes("value") ? token.end : cursor.ch;
        candidates = candidates.filter(x => x.startsWith(word));
        if (candidates.length > 0 && !(candidates.length == 1 && candidates[0] == word)) {
          return {
            list: candidates,
            from: CodeMirror.Pos(cursor.line, start),
            to: CodeMirror.Pos(cursor.line, end)
          }
        }
      }
    }
    return null;
  });
  
  function regexToPossibleValues(regex, opening) {
    if (regex instanceof Array) {
      if (opening != "(" && opening != "[" && opening) {
        throw new Error("illegal argument");
      }
      var values = [];
      while (true) {
        if (regex.length == 0) {
          return values;
        }
        var c = regex[0];
        var escape = false;
        if (c == "\\") {
          regex.shift();
          if (regex.length == 0) {
            throw new Error();
          }
          escape = true;
          c = regex[0];
        }
        if (opening == "[") {
          if (escape) {
            regex.shift();
            values.push(c);
          } else if (c == "]") {
            if (values.length == 0) {
              throw new Error();
            }
            return values;
          } else if (c == "-") {
            if (values.length == 0 || regex.length <= 1 || regex[1] == "]") {
              throw new Error("todo");
            } else if (regex[1] == "^" ||
                       regex[1] == "\\" ||
                       regex[1] == "?" ||
                       regex[1] == "$" ||
                       regex[1] == "*" ||
                       regex[1] == "+" ||
                       regex[1] == "." ||
                       regex[1] == "-" ||
                       regex[1] == "|" ||
                       regex[1] == "[" ||
                       regex[1] == "(" ||
                       regex[1] == ")" ||
                       regex[1] == "{" ||
                       regex[1] == "}") {
              throw new Error("todo");
            } else {
              regex.shift();
              var c1 = values[values.length - 1].codePointAt(0);
              var c2 = regex.shift().codePointAt(0);
              if (c2 <= c1) {
                throw new Error();
              }
              for (var i = c1 + 1; i <= c2; i++) {
                values.push(String.fromCodePoint(i));
              }
            }
          } else if (c == "^" ||
                     c == "?" ||
                     c == "$" ||
                     c == "*" ||
                     c == "+" ||
                     c == "." ||
                     c == "|" ||
                     c == "[" ||
                     c == "(" ||
                     c == ")" ||
                     c == "{" ||
                     c == "}") {
            throw new Error("todo");
          } else {
            regex.shift();
            values.push(c);
          }
        } else if (escape) {
          regex.shift();
          if (values.length == 0) {
            values.push(c);
          } else {
            for (var i = 0; i < values.length; i++) {
              values[i] += c;
            }
          }
        } else if (opening == "(" && c == ")") {
          return values;
        } else if (c == "(" || c == "[") {
          regex.shift();
          var v = regexToPossibleValues(regex, c);
          if (regex.length == 0 || (c == "(" && regex[0] != ")" || c == "[" && regex[0] != "]")) {
            throw new Error("unmatched parentheses");
          }
          regex.shift();
          if (values.length == 0) {
            values = v;
          } else {
            var newValues = [];
            for (var i = 0; i < values.length; i++) {
              for (var j = 0; j < v.length; j++) {
                newValues.push(values[i] + v[j]);
              }
            }
            values = newValues;
          }
        } else if (c == "|") {
          regex.shift();
          values = values.concat(regexToPossibleValues(regex, opening));
        } else if (c == "^" && !opening && values.length == 0) {
          regex.shift();
        } else if (c == "$" && !opening && regex.length == 1) {
          regex.shift();
        } else if (c == "^" ||
                   c == "?" ||
                   c == "$" ||
                   c == "*" ||
                   c == "+" ||
                   c == "." ||
                   c == "]" ||
                   c == ")" ||
                   c == "{" ||
                   c == "}") {
          throw new Error("todo");
        } else {
          regex.shift();
          if (values.length == 0) {
            values.push(c);
          } else {
            for (var i = 0; i < values.length; i++) {
              values[i] += c;
            }
          }
        }
      }
      if (values.length == 0) {
        throw new Error();
      }
      if (opening) {
        throw new Error();
      }
      return values;
    } else if (regex instanceof RegExp) {
      return regexToPossibleValues(regex.toString().slice(1, -1), opening);
    } else { // String
      var array = [];
      for (var i = 0, len = regex.length; i < len; i++) {
        array.push(regex.charAt(i));
      }
      return regexToPossibleValues(array, opening);
    }
  }
});
