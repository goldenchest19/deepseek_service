TERM_NORMALIZER = {
    # Языки программирования
    'python': 'python',
    'пайтон': 'python',
    'java': 'java',
    'javascript': 'javascript',
    'js': 'javascript',
    'typescript': 'typescript',
    'ts': 'typescript',
    'c++': 'c++',
    'с++': 'c++',  # кириллическая С
    'c#': 'c#',
    'с#': 'c#',  # кириллическая С
    'go': 'go',
    'golang': 'go',
    'php': 'php',
    'ruby': 'ruby',
    'swift': 'swift',
    'kotlin': 'kotlin',
    'scala': 'scala',
    'rust': 'rust',
    'r': 'r',
    'bash': 'bash',
    'powershell': 'powershell',
    'perl': 'perl',
    'objective-c': 'objective-c',
    'objective c': 'objective-c',
    'haskell': 'haskell',
    'clojure': 'clojure',
    'erlang': 'erlang',
    'dart': 'dart',
    'flutter': 'flutter',
    'elixir': 'elixir',
    'cobol': 'cobol',
    'fortran': 'fortran',
    'groovy': 'groovy',
    'assembly': 'assembly',
    'ассемблер': 'assembly',
    'pascal': 'pascal',
    'delphi': 'delphi',
    'prolog': 'prolog',

    # Базы данных
    'sql': 'sql',
    'postgresql': 'postgresql_sql',
    'postgres': 'postgresql_sql',
    'mysql': 'mysql_sql',
    'mariadb': 'mysql_sql',
    'sqlite': 'sqlite_sql',
    'mongodb': 'mongodb',
    'mongo': 'mongodb',
    'redis': 'redis',
    'cassandra': 'cassandra',
    'elasticsearch': 'elasticsearch',
    'opensearch': 'opensearch',
    'neo4j': 'neo4j',
    'graphdb': 'neo4j',
    'hbase': 'hbase',
    'dynamodb': 'dynamodb',
    'cosmosdb': 'cosmosdb',
    'couchdb': 'couchdb',
    'oracle': 'oracle',
    'mssql': 'mssql',
    'sqlserver': 'mssql',
    'firebird': 'firebird',
    'clickhouse': 'clickhouse',
    'influxdb': 'influxdb',
    'cockroachdb': 'cockroachdb',
    'rethinkdb': 'rethinkdb',
    'vertica': 'vertica',
    'snowflake': 'snowflake',
    'greenplum': 'greenplum',
    'teradata': 'teradata',
    'dgraph': 'dgraph',
    'bigtable': 'bigtable',
    'redshift': 'redshift',
    'postgresql_sql': 'postgresql_sql',
    'mysql_sql': 'mysql_sql',
    'sqlite_sql': 'sqlite_sql',

    # Фреймворки и библиотеки
    'django': 'django',
    'fastapi': 'fastapi',
    'flask': 'flask',
    'spring': 'spring',
    'springboot': 'spring',
    'springframework': 'spring',
    'spring boot': 'spring',
    'spring framework': 'spring',
    'hibernate': 'hibernate',
    'react': 'react',
    'reactjs': 'react',
    'vue': 'vue',
    'vuejs': 'vue',
    'angular': 'angular',
    'angularjs': 'angular',
    'express': 'express',
    'expressjs': 'express',
    'nest': 'nest',
    'nestjs': 'nest',
    'aspnet': 'aspnet',
    'asp.net': 'aspnet',
    'dotnet': 'dotnet',
    '.net': 'dotnet',
    'wpf': 'wpf',
    'rails': 'rails',
    'rubyonrails': 'rails',
    'laravel': 'laravel',
    'symfony': 'symfony',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'scikit-learn': 'scikit-learn',
    'sklearn': 'scikit-learn',
    'tensorflow': 'tensorflow',
    'tf': 'tensorflow',
    'pytorch': 'pytorch',
    'torch': 'pytorch',
    'keras': 'keras',
    'pyspark': 'pyspark',
    'hadoop': 'hadoop',
    'spark': 'spark',
    'junit': 'junit',
    'testng': 'testng',
    'jest': 'jest',
    'mocha': 'mocha',
    'pytest': 'pytest',
    'selenium': 'selenium',
    'cypress': 'cypress',
    'cucumber': 'cucumber',
    'bootstrap': 'bootstrap',
    'jquery': 'jquery',
    'redux': 'redux',
    'rxjs': 'rxjs',
    'backbone': 'backbone',
    'svelte': 'svelte',
    'ember': 'ember',
    'emberjs': 'ember',
    'next': 'next',
    'nextjs': 'next',
    'nuxt': 'nuxt',
    'nuxtjs': 'nuxt',
    'gatsby': 'gatsby',
    'gatsbyjs': 'gatsby',
    'tailwind': 'tailwind',
    'tailwindcss': 'tailwind',
    'sass': 'sass',
    'scss': 'sass',
    'less': 'less',
    'stylus': 'stylus',
    'webpack': 'webpack',
    'babel': 'babel',
    'parcel': 'parcel',
    'rollup': 'rollup',
    'eslint': 'eslint',
    'prettier': 'prettier',
    'stylelint': 'stylelint',
    'sentry': 'sentry',
    'nextjs': 'nextjs',
    'socketio': 'socketio',
    'websocket': 'websocket',
    'webrtc': 'webrtc',
    'graphene': 'graphene',
    'apollo': 'apollo',
    'gqlgen': 'gqlgen',
    'relay': 'relay',
    'remix': 'remix',

    # Контроль версий
    'git': 'git',
    'github': 'git',
    'gitlab': 'git',
    'bitbucket': 'git',
    'svn': 'svn',
    'subversion': 'svn',
    'mercurial': 'mercurial',
    'hg': 'mercurial',
    'perforce': 'perforce',

    # Контейнеризация и оркестрация
    'docker': 'docker',
    'kubernetes': 'kubernetes',
    'k8s': 'kubernetes',
    'helm': 'helm',
    'openshift': 'openshift',
    'oc': 'openshift',
    'istio': 'istio',
    'podman': 'podman',
    'containerd': 'containerd',
    'docker-compose': 'docker-compose',
    'swarm': 'swarm',
    'docker swarm': 'swarm',
    'linkerd': 'linkerd',
    'consul': 'consul',
    'nomad': 'nomad',
    'rancher': 'rancher',
    'mesos': 'mesos',
    'knative': 'knative',
    'portainer': 'portainer',

    # CI/CD
    'jenkins': 'jenkins',
    'gitlab-ci': 'gitlab-ci',
    'github-actions': 'github-actions',
    'circleci': 'circleci',
    'travis': 'travis',
    'travisci': 'travis',
    'teamcity': 'teamcity',
    'bamboo': 'bamboo',
    'gocd': 'gocd',
    'argo': 'argo',
    'argocd': 'argo',
    'tekton': 'tekton',
    'concourse': 'concourse',
    'spinnaker': 'spinnaker',
    'jenkins x': 'jenkins-x',
    'woodpecker': 'woodpecker',
    'drone': 'drone',
    'codeship': 'codeship',
    'semaphore': 'semaphore',
    'gitlab ci': 'gitlab-ci',
    'github actions': 'github-actions',
    'travis ci': 'travis',
    'jenkins-x': 'jenkins-x',

    # Облачные провайдеры и платформы
    'aws': 'aws',
    'amazon': 'aws',
    'amazon web services': 'aws',
    'azure': 'azure',
    'microsoft azure': 'azure',
    'gcp': 'gcp',
    'google cloud': 'gcp',
    'google cloud platform': 'gcp',
    'heroku': 'heroku',
    'digitalocean': 'digitalocean',
    'do': 'digitalocean',
    'linode': 'linode',
    'vultr': 'vultr',
    'ibm cloud': 'ibm-cloud',
    'oracle cloud': 'oracle-cloud',
    'oci': 'oracle-cloud',
    'alibaba cloud': 'alibaba-cloud',
    'aliyun': 'alibaba-cloud',
    'cloudflare': 'cloudflare',
    'scaleway': 'scaleway',
    'openstack': 'openstack',
    'ovh': 'ovh',
    'hetzner': 'hetzner',
    'netlify': 'netlify',
    'vercel': 'vercel',
    'serverless': 'serverless',
    'lambda': 'lambda',
    'ec2': 'ec2',
    's3': 's3',
    'route53': 'route53',
    'cloudfront': 'cloudfront',
    'ecs': 'ecs',
    'eks': 'eks',
    'rds': 'rds',
    'dynamodb': 'dynamodb',
    'sqs': 'sqs',
    'sns': 'sns',
    'cloudwatch': 'cloudwatch',
    'iam': 'iam',
    'vpc': 'vpc',
    'azuredevops': 'azuredevops',
    'azure devops': 'azuredevops',
    'gke': 'gke',
    'gcf': 'gcf',
    'gcs': 'gcs',
    'ibm-cloud': 'ibm-cloud',
    'oracle-cloud': 'oracle-cloud',
    'alibaba-cloud': 'alibaba-cloud',

    # Коммуникационные протоколы и APIs
    'rest': 'rest',
    'restful': 'rest',
    'graphql': 'graphql',
    'grpc': 'grpc',
    'soap': 'soap',
    'webhook': 'webhook',
    'websocket': 'websocket',
    'mqtt': 'mqtt',
    'amqp': 'amqp',
    'stomp': 'stomp',
    'tcp': 'tcp',
    'udp': 'udp',
    'http': 'http',
    'https': 'https',
    'http/2': 'http2',
    'http2': 'http2',
    'http/3': 'http3',
    'http3': 'http3',
    'quic': 'quic',
    'ftp': 'ftp',
    'sftp': 'sftp',
    'ssh': 'ssh',
    'telnet': 'telnet',
    'dns': 'dns',
    'dhcp': 'dhcp',
    'smtp': 'smtp',
    'pop3': 'pop3',
    'imap': 'imap',
    'ldap': 'ldap',
    'oauth': 'oauth',
    'oauth2': 'oauth2',
    'openid': 'openid',
    'openid connect': 'openid',
    'saml': 'saml',
    'kerberos': 'kerberos',
    'rpc': 'rpc',
    'jsonrpc': 'jsonrpc',
    'xmlrpc': 'xmlrpc',
    'thrift': 'thrift',
    'avro': 'avro',
    'protobuf': 'protobuf',
    'messagepack': 'messagepack',
    'json': 'json',
    'xml': 'xml',
    'yaml': 'yaml',
    'yml': 'yaml',
    'toml': 'toml',
    'ini': 'ini',
    'csv': 'csv',
    'tsv': 'tsv',
    'parquet': 'parquet',
    'orc': 'orc',
    'swagger': 'swagger',
    'openapi': 'openapi',
    'raml': 'raml',
    'ipfs': 'ipfs',
    'bittorrent': 'bittorrent',

    # Мониторинг, логирование и трейсинг
    'prometheus': 'prometheus',
    'grafana': 'grafana',
    'kibana': 'kibana',
    'elasticsearch': 'elasticsearch',
    'logstash': 'logstash',
    'fluentd': 'fluentd',
    'loki': 'loki',
    'datadog': 'datadog',
    'newrelic': 'newrelic',
    'new relic': 'newrelic',
    'sentry': 'sentry',
    'jaeger': 'jaeger',
    'zipkin': 'zipkin',
    'dynatrace': 'dynatrace',
    'splunk': 'splunk',
    'nagios': 'nagios',
    'zabbix': 'zabbix',
    'influxdb': 'influxdb',
    'telegraf': 'telegraf',
    'elk': 'elk',
    'elastic stack': 'elk',
    'graylog': 'graylog',
    'sumo logic': 'sumologic',
    'sumologic': 'sumologic',
    'graphite': 'graphite',
    'statsd': 'statsd',
    'opentelemetry': 'opentelemetry',
    'opentracing': 'opentracing',
    'elk stack': 'elk',

    # Очереди сообщений и брокеры
    'kafka': 'kafka',
    'rabbitmq': 'rabbitmq',
    'activemq': 'activemq',
    'zeromq': 'zeromq',
    'zmq': 'zeromq',
    'redis': 'redis',
    'nats': 'nats',
    'pulsar': 'pulsar',
    'nsq': 'nsq',
    'mosquitto': 'mosquitto',
    'ibm mq': 'ibmmq',
    'ibmmq': 'ibmmq',
    'servicebus': 'servicebus',
    'azure service bus': 'servicebus',
    'eventbridge': 'eventbridge',
    'aws eventbridge': 'eventbridge',
    'pubsub': 'pubsub',
    'google pubsub': 'pubsub',
    'sqs': 'sqs',
    'sns': 'sns',
    'kinesis': 'kinesis',
    'aws kinesis': 'kinesis',
    'event hub': 'eventhub',
    'azure event hub': 'eventhub',
    'eventhub': 'eventhub',

    # Языки
    'английский': 'english',
    'английского': 'english',
    'англ': 'english',
    'english': 'english',
    'немецкий': 'german',
    'французский': 'french',
    'испанский': 'spanish',
    'итальянский': 'italian',
    'китайский': 'chinese',
    'японский': 'japanese',

    # Методологии и практики
    'agile': 'agile',
    'scrum': 'scrum',
    'kanban': 'kanban',
    'devops': 'devops',
    'ci/cd': 'ci/cd',
    'cicd': 'ci/cd',
    'tdd': 'tdd',
    'bdd': 'bdd',
    'ddd': 'ddd',
    'xp': 'xp',
    'extreme programming': 'xp',
    'lean': 'lean',
    'waterfall': 'waterfall',
    'итеративный': 'iterative',
    'итеративная': 'iterative',
    'iterative': 'iterative',
    'ооп': 'oop',
    'oops': 'oop',
    'oop': 'oop',
    'devops': 'devops',
    'sre': 'sre',
    'devsecops': 'devsecops',
    'gitflow': 'gitflow',
    'trunk-based': 'trunk-based',
    'trunk based': 'trunk-based',
    'монолит': 'monolith',
    'monolith': 'monolith',
    'microservices': 'microservices',
    'микросервисы': 'microservices',
    'serverless': 'serverless',
    'безсерверный': 'serverless',
    'iac': 'iac',
    'infrastructure as code': 'iac',
    'codeowners': 'codeowners',
    'сode review': 'code-review',
    'peer review': 'code-review',
    'code-review': 'code-review',
    'pair programming': 'pair-programming',
    'safe': 'safe',
    'scaled agile': 'safe',
    'mob programming': 'mob-programming',
    'continuous integration': 'ci',
    'continuous delivery': 'cd',
    'continuous deployment': 'cd'
}
